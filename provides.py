from charms.reactive import (
    toggle_flag,
    Endpoint,
)


class PrometheusManualProvides(Endpoint):

    def manage_flags(self):
        super().manage_flags()
        toggle_flag(self.expand_name('endpoint.{endpoint_name}.available'),
                    self.is_joined)
                    #self.is_joined and self.requests)

    def register_job(
        self,
        job_name,
        job_data,
        ca_cert=None,
        client_cert=None,
        client_key=None,
        relation=None,
    ):
        """
        Register a manual job.

        The job data should be the (unserialized) data defining the job.

        To ensure uniqueness, a UUID will be added to the job name, and it will
        be injected into the job data.

        If a CA cert is given, the value of any ca_file field in the job data
        will be replaced with a filename after the CA cert data is written, so
        a placeholder value should be used.

        If a client cert and key are given, the value of any cert_file/key_file
        fields in the job data will be replaced with filenames pointing to the
        corresponding files after there data is written.

        If a specific relation is not given, the job will be registered with
        every related Prometheus.
        """
        # we might be connected to multiple prometheuses for some strange
        # reason, so just send the job to all of them
        relations = [relation] if relation is not None else self.relations
        for relation in relations:
            relation.to_publish_app['job_'+job_name] = {
                'job_name': job_name,
                'job_data': job_data,
                'ca_cert': ca_cert,
                'client_cert': client_cert,
                'client_key': client_key
            }
            relation._flush_data()
