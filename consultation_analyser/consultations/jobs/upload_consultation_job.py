from django_rq import job

@job('default')
def upload_consultation():
    pass
