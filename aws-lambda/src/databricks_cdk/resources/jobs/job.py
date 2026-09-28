import json
import logging
from typing import Dict, List, Optional, Union

import requests
from pydantic import BaseModel

from databricks_cdk.utils import CnfResponse, get_authorization_headers, post_request

logger = logging.getLogger(__name__)


class JobEmailNotifications(BaseModel):
    on_start: List[str] = []
    on_success: List[str] = []
    on_failure: List[str] = []
    no_alert_for_skipped_runs: bool = False


class AutoScale(BaseModel):
    min_workers: int
    max_workers: int


class AwsAttributes(BaseModel):
    first_on_demand: Optional[int] = None
    availability: Optional[str] = None
    zone_id: Optional[str] = None
    instance_profile_arn: Optional[str] = None
    spot_bid_price_percent: Optional[int] = None
    ebs_volume_type: Optional[str] = None
    ebs_volume_count: Optional[int] = None
    ebs_volume_size: Optional[int] = None
    ebs_volume_iops: Optional[int] = None
    ebs_volume_throughput: Optional[int] = None


class DockerBasicAuth(BaseModel):
    username: str
    password: str


class DockerImage(BaseModel):
    url: str
    basic_auth: Optional[DockerBasicAuth]


class NewCluster(BaseModel):
    num_workers: Optional[int] = None
    autoscale: Optional[AutoScale] = None
    spark_version: str
    docker_image: Optional[DockerImage] = None
    spark_conf: Dict[str, str] = {}
    aws_attributes: AwsAttributes
    node_type_id: Optional[str] = None
    driver_node_type_id: Optional[str] = None
    ssh_public_keys: List[str] = []
    custom_tags: Optional[dict] = None
    cluster_log_conf: Optional[dict] = None
    init_scripts: List[dict] = []
    spark_env_vars: Dict[str, str] = {}
    enable_elastic_disk: Optional[bool] = None
    driver_instance_pool_id: Optional[str] = None
    instance_pool_id: Optional[str] = None
    data_security_mode: Optional[str] = None
    runtime_engine: Optional[str] = None


class JobCluster(BaseModel):
    job_cluster_key: str
    new_cluster: NewCluster


class NotebookTask(BaseModel):
    notebook_path: str
    base_parameters: dict = {}


class SparkJarTask(BaseModel):
    main_class_name: str
    parameters: List[str] = []


class SparkPythonTask(BaseModel):
    python_file: str
    parameters: List[str] = []


class SparkSubmitTask(BaseModel):
    parameters: List[str] = []


class PipelineTask(BaseModel):
    pipeline_id: str


class PythonWheelTask(BaseModel):
    package_name: str
    entry_point: Optional[str] = None
    parameters: List[str] = []


class Library(BaseModel):
    jar: Optional[str] = None
    egg: Optional[str] = None
    whl: Optional[str] = None
    pypi: Optional[str] = None
    maven: Optional[str] = None
    cran: Optional[str] = None


class RunJobTask(BaseModel):
    job_id: int
    job_parameters: Optional[Dict[str, str]] = None
    python_params: Optional[List[str]] = None
    notebook_params: Optional[Dict[str, str]] = None
    jar_params: Optional[List[str]] = None
    spark_submit_params: Optional[List[str]] = None


class ConditionTask(BaseModel):
    left: str
    op: str
    right: str


class ForEachTask(BaseModel):
    inputs: str
    task: "JobTaskSettings"
    concurrency: Optional[int] = None


class TaskDependency(BaseModel):
    task_key: str
    outcome: Optional[str] = None


class JobsHealthRule(BaseModel):
    metric: str
    op: str
    value: int


class JobsHealth(BaseModel):
    rules: List[JobsHealthRule] = []


class WebhookNotificationDestination(BaseModel):
    id: str


class WebhookNotifications(BaseModel):
    on_start: Optional[List[WebhookNotificationDestination]] = None
    on_success: Optional[List[WebhookNotificationDestination]] = None
    on_failure: Optional[List[WebhookNotificationDestination]] = None
    on_duration_warning_threshold_exceeded: Optional[List[WebhookNotificationDestination]] = None
    on_streaming_backlog_exceeded: Optional[List[WebhookNotificationDestination]] = None


class TaskNotificationSettings(BaseModel):
    no_alert_for_skipped_runs: Optional[bool] = None
    no_alert_for_canceled_runs: Optional[bool] = None
    alert_on_last_attempt: Optional[bool] = None


class JobTaskSettings(BaseModel):
    task_key: str
    description: Optional[str] = None
    depends_on: List[TaskDependency] = []
    run_if: Optional[str] = None
    existing_cluster_id: Optional[str] = None
    new_cluster: Optional[NewCluster] = None
    job_cluster_key: Optional[str] = None
    notebook_task: Optional[NotebookTask] = None
    spark_jar_task: Optional[SparkJarTask] = None
    spark_python_task: Optional[SparkPythonTask] = None
    spark_submit_task: Optional[SparkSubmitTask] = None
    pipeline_task: Optional[PipelineTask] = None
    python_wheel_task: Optional[PythonWheelTask] = None
    run_job_task: Optional[RunJobTask] = None
    condition_task: Optional[ConditionTask] = None
    for_each_task: Optional[ForEachTask] = None
    libraries: List[Library] = []
    email_notifications: Optional[JobEmailNotifications] = None
    webhook_notifications: Optional[WebhookNotifications] = None
    notification_settings: Optional[TaskNotificationSettings] = None
    health: Optional[JobsHealth] = None
    environment_key: Optional[str] = None
    timeout_seconds: Optional[int] = None
    max_retries: Optional[int] = None
    min_retry_interval_millis: Optional[int] = None
    retry_on_timeout: bool = False


ForEachTask.update_forward_refs()


class CronSchedule(BaseModel):
    quartz_cron_expression: Optional[str] = None
    timezone_id: Optional[str] = None
    pause_status: Optional[str] = None


class FileArrivalTriggerConfiguration(BaseModel):
    url: str
    min_time_between_triggers_seconds: Optional[int] = None
    wait_after_last_change_seconds: Optional[int] = None


class TableUpdateTriggerConfiguration(BaseModel):
    table_names: List[str] = []
    condition: Optional[str] = None
    min_time_between_triggers_seconds: Optional[int] = None
    wait_after_last_change_seconds: Optional[int] = None


class PeriodicTriggerConfiguration(BaseModel):
    interval: int
    unit: str


class TriggerSettings(BaseModel):
    pause_status: Optional[str] = None
    file_arrival: Optional[FileArrivalTriggerConfiguration] = None
    table_update: Optional[TableUpdateTriggerConfiguration] = None
    periodic: Optional[PeriodicTriggerConfiguration] = None


class ContinuousSettings(BaseModel):
    pause_status: Optional[str] = None


class QueueSettings(BaseModel):
    enabled: bool


class JobParameterDefinition(BaseModel):
    name: str
    default: str


class AccessControlRequestForUser(BaseModel):
    user_name: str
    permission_level: str


class AccessControlRequestForGroup(BaseModel):
    group_name: str
    permission_level: str


class JobSettings(BaseModel):
    name: str
    description: Optional[str] = None
    tasks: List[JobTaskSettings]
    job_clusters: List[JobCluster] = []
    email_notifications: Optional[JobEmailNotifications] = None
    webhook_notifications: Optional[WebhookNotifications] = None
    notification_settings: Optional[TaskNotificationSettings] = None
    health: Optional[JobsHealth] = None
    timeout_seconds: Optional[int] = None
    schedule: Optional[CronSchedule] = None
    trigger: Optional[TriggerSettings] = None
    continuous: Optional[ContinuousSettings] = None
    queue: Optional[QueueSettings] = None
    parameters: Optional[List[JobParameterDefinition]] = None
    tags: Optional[Dict[str, str]] = None
    max_concurrent_runs: Optional[int] = None
    format: str = "MULTI_TASK"
    access_control_list: Optional[List[Union[AccessControlRequestForUser, AccessControlRequestForGroup]]] = None


class JobProperties(BaseModel):
    action: str = "job"
    workspace_url: str
    job: JobSettings


class JobResponse(CnfResponse):
    job_id: int


def get_job_url(workspace_url: str):
    """Getting url for job requests"""
    return f"{workspace_url}/api/2.1/jobs"


def get_job_by_id(job_id: str, workspace_url: str):
    body = {"job_id": job_id}
    resp = requests.get(
        f"{get_job_url(workspace_url)}/get",
        json=body,
        headers=get_authorization_headers(),
    )
    if resp.status_code == 400 and "does not exist" in resp.text:
        return None
    resp.raise_for_status()
    return resp.json()


def job_settings_body(job: JobSettings) -> dict:
    """Serialise job settings without unset fields, so each task carries only its own type"""
    return json.loads(job.json(exclude_none=True))


def create_or_update_job(properties: JobProperties, physical_resource_id: Optional[str]) -> JobResponse:
    """Create job at databricks"""
    current: Optional[dict] = None
    url = get_job_url(properties.workspace_url)
    if physical_resource_id is not None:
        current = get_job_by_id(physical_resource_id, properties.workspace_url)
    if current is None:
        create_response = post_request(f"{url}/create", body=job_settings_body(properties.job))
        job_id = create_response.get("job_id")
        return JobResponse(job_id=job_id, physical_resource_id=job_id)
    else:
        job_id = current.get("job_id")
        reset_body = {
            "job_id": job_id,
            "new_settings": job_settings_body(properties.job),
        }
        post_request(f"{url}/reset", body=reset_body)
        return JobResponse(job_id=job_id, physical_resource_id=job_id)


def delete_job(properties: JobProperties, physical_resource_id: str) -> CnfResponse:
    """Deletes job at databricks"""
    current = get_job_by_id(physical_resource_id, properties.workspace_url)
    if current is not None:
        url = get_job_url(properties.workspace_url)
        post_request(f"{url}/delete", body={"job_id": current.get("job_id")})
    else:
        logger.warning("Already removed")
    return CnfResponse(physical_resource_id=physical_resource_id)
