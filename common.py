import json
from copy import deepcopy
from pathlib import Path
from hashlib import sha1

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

    def to_json(self):
        """
        Render the job request to JSON string which can be included directly
        into Prometheus config.

        Keys will be sorted in the rendering to ensure a stable ordering for
        comparisons to detect changes.
        """
        job_data = deepcopy(self.job_data)  # make a copy we can modify
        job_data['job_name'] = '{}-{}'.format(self.job_name, self.request_id)

        if self.ca_cert:
            # cert has to be provided in a file, so we need to stash it on disk
            # FIXME: this should probably be provided by the charm, but it also
            # needs to be populated into the JSON data
            cert_dir = Path('/var/snap/prometheus/common/certs')
            cert_dir.mkdir(parents=True, exist_ok=True)

            # use a hash of the cert data rather than the request ID so that we
            # can detect changes to the data via the filename
            cert_hash = sha1(self.ca_cert.encode('utf8')).hexdigest()
            cert_path = cert_dir / '{}-{}.crt'.format(self.job_name, cert_hash)
            cert_path.write_text(self.ca_cert + '\n')

            for key, value in job_data.items():
                # update the cert path at the job level
                if key == 'tls_config':
                    value['ca_file'] = str(cert_path)

                # update the cert path at the SD config level
                if key.endswith('_sd_configs'):
                    for sd_config in value:
                        if 'ca_file' in sd_config.get('tls_config', {}):
                            sd_config['tls_config']['ca_file'] = str(cert_path)

        return json.dumps(job_data, sort_keys=True)

    def respond(self, success, reason=None):
        """
        Acknowledge this request, and indicate success or failure with an
        optional explanation.
        """
        super().respond(success=success, reason=reason)
