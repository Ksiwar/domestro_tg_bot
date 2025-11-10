import ipaddress
import json
import validators
from bson import ObjectId
from pydantic import BaseModel, field_validator
from typing import Optional, List


class NameNotUniqueError(Exception): ...
class IpNotUniqueError(Exception): ...
class HostNotUniqueError(Exception): ...


class Ip(BaseModel):
    ip: str
    name: str
    is_available: Optional[bool] = True

    @field_validator("ip")
    def validate_ip(cls, v: str) -> str:
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError(f"Invalid IP address format input: '{v}'")
        return v

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: lambda v: str(v)}

    def toJson(self):
        return json.dumps(self.model_dump(), default=str)


class Service(BaseModel):
    host: str
    name: str
    is_available: Optional[bool] = True

    @field_validator("host")
    def validate_host(cls, v: str) -> str:
        if validators.domain(v):
            return v
        raise ValueError(f"Invalid url or domain input: '{v}'")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: lambda v: str(v)}

    def toJson(self):
        return json.dumps(self.model_dump(), default=str)


class User(BaseModel):
    name: str
    chat_id: int
    phone_number: str
    first_name : Optional[str] = ""
    last_name: Optional[str] = ""
    is_wants_premium: Optional[bool] = False
    feedbacks: Optional[List[str]] = []
    help: Optional[List[str]] = []
    age: Optional[int] = None
    ips: Optional[List[Ip]] = []
    service: Optional[List[Service]] = []

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: lambda v: str(v)
        }

    def add_feedback(self, feedback: str):
        self.feedbacks.append(feedback)

    def add_ip(self, ip: Ip):
        """Adds an IP address to the user's list of IPs if the name and IP are unique."""
        if any(existing_ip.name == ip.name for existing_ip in self.ips) or any(
                existing_ip.name == ip.name for existing_ip in self.service):
            raise NameNotUniqueError("Name must be unique")
        if any(existing_ip.ip == ip.ip for existing_ip in self.ips):
            raise IpNotUniqueError("IP must be unique")
        self.ips.append(ip)

    def update_ip_by_index(self, index: int, updated_ip: Ip):
        """Updates an IP in the user's list of IPs by index."""
        if self.ips is not None and 0 <= index < len(self.ips):
            # Exclude the current IP from the uniqueness check
            if any(existing_ip.name == updated_ip.name for existing_ip in self.service) or any(
                    existing_ip.name == updated_ip.name for existing_ip in self.ips if existing_ip != self.ips[index]):
                raise NameNotUniqueError("Name must be unique")
            if any(existing_ip.ip == updated_ip.ip for existing_ip in self.ips if existing_ip != self.ips[index]):
                raise IpNotUniqueError("IP must be unique")
            self.ips[index] = updated_ip

    def update_service_by_index(self, index: int, updated_service: Service):
        """Updates a service in the user's list of services by index."""
        if self.service is not None and 0 <= index < len(self.service):
            # Exclude the current service from the uniqueness check
            if any(existing_service.name == updated_service.name for existing_service in self.service if
                   existing_service != self.service[index]) or any(
                    existing_ip.name == updated_service.name for existing_ip in self.ips):
                raise NameNotUniqueError("Name must be unique")
            if any(existing_service.host == updated_service.host for existing_service in self.service if
                   existing_service != self.service[index]):
                raise HostNotUniqueError("Host must be unique")
            self.service[index] = updated_service

    def add_service(self, service: Service):
        """Adds a service to the user's list of services if the name and host are unique."""
        if any(existing_service.name == service.name for existing_service in self.service) or any(
                existing_ip.name == service.name for existing_ip in self.ips):
            raise NameNotUniqueError("Name must be unique")
        if any(existing_service.host == service.host for existing_service in self.service):
            raise HostNotUniqueError("Host must be unique")
        self.service.append(service)

    def delete_ip_by_index(self, index: int):
        """Deletes an IP address from the user's list of IPs by index."""
        if self.ips is not None and 0 <= index < len(self.ips):
            self.ips.pop(index)

    def delete_service_by_index(self, index: int):
        """Deletes a service from the user's list of services by index."""
        if self.service is not None and 0 <= index < len(self.service):
            self.service.pop(index)

    def toJson(self):
        return json.dumps(self.model_dump(), default=str)
