from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field
import os

class Settings(BaseSettings):
    # Procura por .env ou .env.docker
    model_config = SettingsConfigDict(
        env_file=('.env', '.env.docker'),
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")

    # URLs Base
    base_scheduler_url: str = Field(default="http://localhost:8000", validation_alias="BASE_SCHEDULER_URL")
    base_youtube_url: str = Field(default="http://localhost:8001", validation_alias="BASE_YOUTUBE_URL")
    base_instagram_url: str = Field(default="http://localhost:8002", validation_alias="BASE_INSTAGRAM_URL")
    monitoring_url: str = Field(default="http://localhost:8003/action", validation_alias="MONITORING_URL")
    monitoring_event_url: str = Field(default="http://localhost:8003/event", validation_alias="MONITORING_EVENT_URL")
    metrics_url_template: str = Field(default="http://localhost:8003/metrics/{plataforma}", validation_alias="METRICS_URL")

    # Rotas do Monitoring (Endpoints providos por este serviço)
    # Usamos aliases para que o monitoring/app.py possa usar nomes semânticos
    monitoring_action: str = Field(default="/action", validation_alias="MONITORING_ACTION_PATH")
    monitoring_event: str = Field(default="/event", validation_alias="MONITORING_EVENT_PATH")
    monitoring_metrics: str = Field(default="/metrics/{platform}", validation_alias="MONITORING_METRICS_PATH")

    # Rotas do Scheduler
    scheduler_home: str = Field(default="/docs", validation_alias="SCHEDULER_HOME")
    scheduler_campaign: str = Field(default="/start_campaign", validation_alias="SCHEDULER_CAMPAIGN")
    scheduler_set_pause_time: str = Field(default="/set_pause_time", validation_alias="SCHEDULER_SET_PAUSE_TIME")
    scheduler_get_pause_time: str = Field(default="/get_pause_time", validation_alias="SCHEDULER_GET_PAUSE_TIME")
    scheduler_post_campaign_result: str = Field(default="/post_campaign_result", validation_alias="SCHEDULER_POST_CAMPAIGN_RESULT")
    scheduler_get_campaign: str = Field(default="/get_campaign", validation_alias="SCHEDULER_GET_CAMPAIGN")
    
    alt_flag: str = Field(default="/alt_flag", validation_alias="ALT_FLAG")
    get_flag: str = Field(default="/get_flag", validation_alias="GET_FLAG")

    # Rotas do Mock YouTube
    youtube_list_videos: str = Field(default="/list_videos", validation_alias="YOUTUBE_LIST_VIDEOS")
    youtube_like_video: str = Field(default="/like_video", validation_alias="YOUTUBE_LIKE_VIDEO")
    youtube_get_likes: str = Field(default="/get_likes", validation_alias="YOUTUBE_GET_LIKES")

    # Rotas do Mock Instagram
    instagram_list_videos: str = Field(default="/list_videos", validation_alias="INSTAGRAM_LIST_VIDEOS")
    instagram_like_video: str = Field(default="/like_video", validation_alias="INSTAGRAM_LIKE_VIDEO")
    instagram_get_likes: str = Field(default="/get_likes", validation_alias="INSTAGRAM_GET_LIKES")

    # Flags
    flag_threshold: str = Field(default="threshold", validation_alias="FLAG_THRESHOLD")
    flag_dynamic_distribution: str = Field(default="dynamic_distribution", validation_alias="FLAG_DYNAMIC_DISTRIBUTION")
    flag_jitter: str = Field(default="jitter", validation_alias="FLAG_JITTER")
    flag_circuit_breaker: str = Field(default="circuit_breaker", validation_alias="FLAG_CIRCUIT_BREAKER")

    # --- URLs Computadas ---
    
    @computed_field
    @property
    def scheduler_home_url(self) -> str:
        return f"{self.base_scheduler_url.rstrip('/')}/{self.scheduler_home.lstrip('/')}"

    @computed_field
    @property
    def scheduler_campaign_url(self) -> str:
        return f"{self.base_scheduler_url.rstrip('/')}/{self.scheduler_campaign.lstrip('/')}"

    @computed_field
    @property
    def scheduler_result_url(self) -> str:
        return f"{self.base_scheduler_url.rstrip('/')}/{self.scheduler_post_campaign_result.lstrip('/')}"

    @computed_field
    @property
    def youtube_list_url(self) -> str:
        return f"{self.base_youtube_url.rstrip('/')}/{self.youtube_list_videos.lstrip('/')}"

    @computed_field
    @property
    def youtube_like_url(self) -> str:
        return f"{self.base_youtube_url.rstrip('/')}/{self.youtube_like_video.lstrip('/')}"

    @computed_field
    @property
    def youtube_likes_url(self) -> str:
        return f"{self.base_youtube_url.rstrip('/')}/{self.youtube_get_likes.lstrip('/')}"

    @computed_field
    @property
    def instagram_list_url(self) -> str:
        return f"{self.base_instagram_url.rstrip('/')}/{self.instagram_list_videos.lstrip('/')}"

    @computed_field
    @property
    def instagram_like_url(self) -> str:
        return f"{self.base_instagram_url.rstrip('/')}/{self.instagram_like_video.lstrip('/')}"

    @computed_field
    @property
    def instagram_likes_url(self) -> str:
        return f"{self.base_instagram_url.rstrip('/')}/{self.instagram_get_likes.lstrip('/')}"

settings = Settings()
