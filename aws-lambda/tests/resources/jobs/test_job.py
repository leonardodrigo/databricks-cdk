import pytest
from pydantic import ValidationError

from databricks_cdk.resources.jobs.job import (
    JobSettings,
    JobTaskSettings,
    job_settings_body,
)


def run_job_step(task_key: str, job_id: int, after=None) -> dict:
    step = {"task_key": task_key, "run_job_task": {"job_id": job_id}}
    if after:
        step["depends_on"] = [{"task_key": key} for key in after]
    return step


def test_run_job_task_is_parsed():
    task = JobTaskSettings(**run_job_step("gather", 123))

    assert task.run_job_task is not None
    assert task.run_job_task.job_id == 123


def test_depends_on_accepts_objects_and_keeps_the_task_key():
    task = JobTaskSettings(**run_job_step("markdown", 2, after=["gather"]))

    assert [dependency.task_key for dependency in task.depends_on] == ["gather"]


def test_depends_on_rejects_the_old_list_of_strings():
    with pytest.raises(ValidationError):
        JobTaskSettings(task_key="markdown", depends_on=["gather"])


def test_a_job_of_only_run_job_tasks_needs_no_clusters():
    settings = JobSettings(
        name="KeesKnowledgeArticles",
        tasks=[
            run_job_step("gather", 1),
            run_job_step("markdown", 2, after=["gather"]),
            run_job_step("index", 3, after=["markdown"]),
        ],
    )

    assert settings.job_clusters == []
    assert len(settings.tasks) == 3


def test_condition_task_and_outcome_dependency():
    settings = JobSettings(
        name="Linnaeus-Active",
        tasks=[
            {
                "task_key": "need_process",
                "condition_task": {"left": "{{tasks.check.values.need_process}}", "op": "EQUAL_TO", "right": "true"},
            },
            {
                "task_key": "fetch_active_run",
                "depends_on": [{"task_key": "need_process", "outcome": "true"}],
                "run_job_task": {"job_id": 42},
            },
        ],
    )

    dependency = settings.tasks[1].depends_on[0]
    assert dependency.outcome == "true"
    assert settings.tasks[0].condition_task.op == "EQUAL_TO"


def test_for_each_task_nests_a_task():
    task = JobTaskSettings(
        task_key="per_table",
        for_each_task={
            "inputs": "{{tasks.list_tables.values.tables}}",
            "concurrency": 4,
            "task": {"task_key": "sync", "run_job_task": {"job_id": 7}},
        },
    )

    assert task.for_each_task.concurrency == 4
    assert task.for_each_task.task.run_job_task.job_id == 7


def test_table_update_trigger_with_condition():
    settings = JobSettings(
        name="Postman-Daily-Pre-Auction",
        tasks=[run_job_step("dwh_daily", 1)],
        trigger={
            "table_update": {
                "table_names": ["databricks.datascience.buzzybee.trade_items"],
                "condition": "ALL_UPDATED",
            }
        },
    )

    assert settings.trigger.table_update.condition == "ALL_UPDATED"


def test_webhook_notifications_health_queue_and_parameters():
    settings = JobSettings(
        name="WithExtras",
        tasks=[run_job_step("only", 1)],
        webhook_notifications={"on_failure": [{"id": "slack-destination"}]},
        health={"rules": [{"metric": "RUN_DURATION_SECONDS", "op": "GREATER_THAN", "value": 1800}]},
        queue={"enabled": True},
        parameters=[{"name": "execution_date", "default": ""}],
        tags={"Team": "DataScience"},
    )

    assert settings.webhook_notifications.on_failure[0].id == "slack-destination"
    assert settings.health.rules[0].value == 1800
    assert settings.queue.enabled is True
    assert settings.parameters[0].name == "execution_date"
    assert settings.tags == {"Team": "DataScience"}


def test_body_omits_unset_fields_so_task_type_is_unambiguous():
    settings = JobSettings(name="Chain", tasks=[run_job_step("gather", 1)])

    body = job_settings_body(settings)
    task = body["tasks"][0]

    assert "run_job_task" in task
    assert "spark_python_task" not in task
    assert "notebook_task" not in task
    assert "condition_task" not in task
    assert "schedule" not in body
    assert "trigger" not in body


def test_body_keeps_fields_that_have_non_none_defaults():
    settings = JobSettings(name="Chain", tasks=[run_job_step("gather", 1)])

    body = job_settings_body(settings)

    assert body["format"] == "MULTI_TASK"
    assert body["job_clusters"] == []


def test_body_round_trips_a_full_orchestration_job():
    settings = JobSettings(
        name="KeesKnowledgeArticles",
        tasks=[
            run_job_step("gather", 1),
            run_job_step("markdown", 2, after=["gather"]),
        ],
        schedule={"quartz_cron_expression": "0 0 6 ? * MON", "timezone_id": "Europe/Amsterdam"},
        webhook_notifications={"on_failure": [{"id": "slack"}]},
        timeout_seconds=7200,
        max_concurrent_runs=1,
        queue={"enabled": True},
    )

    body = job_settings_body(settings)

    assert body["tasks"][1]["depends_on"] == [{"task_key": "gather"}]
    assert body["tasks"][1]["run_job_task"]["job_id"] == 2
    assert body["schedule"]["quartz_cron_expression"] == "0 0 6 ? * MON"
    assert body["webhook_notifications"]["on_failure"] == [{"id": "slack"}]
    assert body["timeout_seconds"] == 7200
