import json
from copy import deepcopy

from charms.reactive import BaseRequest, BaseResponse, Field


class JobResponse(BaseResponse):
    success = Field('Whether or not the registration succeeded')
    reason = Field('If failed, a description of why')


class JobRequest(BaseRequest):
    RESPONSE_CLASS = JobResponse

    job_name = Field('Desired name for the job.  To ensure uniqueness, the '
                     'the request ID will be appended to the final job name.')

    job_data = Field('Config data for the job.')

    ca_cert = Field('Cert data for the CA used to validate connections.')

    client_cert = Field('Cert data for the client used to make connections.')

    client_key = Field('Key data for the client used to make connections.')

    def to_json(self, ca_file=None, cert_file=None, key_file=None):
        """
        Render the job request to JSON string which can be included directly
        into Prometheus config.

        Keys will be sorted in the rendering to ensure a stable ordering for
        comparisons to detect changes.

        If `ca_file` is given, it will be used to replace the value of any
        `ca_file` fields in the job.

        If `cert_file` and `key_file` are given, they will be used to replace
        the value of any `cert_file` and `key_file` fields in the job.

        The charm should ensure that the request's `ca_cert`, `client_cert`
        and `client_key` data is writen to those paths prior to calling this
        method.
        """
        job_data = deepcopy(self.job_data)  # make a copy we can modify
        job_data['job_name'] = '{}-{}'.format(self.job_name, self.request_id)

        if ca_file:
            for key, value in job_data.items():
                # update the cert path at the job level
                if key == 'tls_config':
                    value['ca_file'] = str(ca_file)

                # update the cert path at the SD config level
                if key.endswith('_sd_configs'):
                    for sd_config in value:
                        sd_tls_config = sd_config.get('tls_config', {})
                        if not sd_tls_config:
                            continue
                        if 'ca_file' in sd_tls_config:
                            sd_tls_config['ca_file'] = str(ca_file)

        if cert_file and key_file:
            for key, value in job_data.items():
                # update the cert/key paths at the job level
                if key == 'tls_config':
                    value['cert_file'] = str(cert_file)
                    value['key_file'] = str(key_file)

                # update the cert/key paths at the SD config level
                if key.endswith('_sd_configs'):
                    for sd_config in value:
                        sd_tls_config = sd_config.get('tls_config', {})
                        if not sd_tls_config:
                            continue
                        if 'client_file' in sd_tls_config:
                            sd_tls_config['cert_file'] = str(cert_file)
                        elif 'key_file' in sd_tls_config:
                            sd_tls_config['key_file'] = str(key_file)

        return json.dumps(job_data, sort_keys=True)

    def respond(self, success, reason=None):
        """
        Acknowledge this request, and indicate success or failure with an
        optional explanation.
        """
        super().respond(success=success, reason=reason)
