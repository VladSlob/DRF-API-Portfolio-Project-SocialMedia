from celery import shared_task
from app.models import Post


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def publish_post(post_id):
    post = Post.objects.get(pk=post_id)
    if post:
        post.is_published = True
        post.save()
    return f"post #{post_id} has been published"


#  docker run -d -p 6379:6379 redis

# celery -A api_config worker --loglevel=INFO --pool=solo
