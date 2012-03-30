import logging
import urllib
import urllib2

from django.conf import settings

from reviewboard.reviews.models import ReviewRequest
from reviewboard.reviews.signals import review_request_published

RDIO_REPOSITORY = 'rdio'

def review_request_published_cb(sender, user, review_request, changedesc, **kwargs):
  # Don't hit any URLs if the review request is discarded or not yet public.
  if not review_request.public or review_request.status == 'D':
    logging.info("Not hitting our jenkins web hook because the review is private.")
    return

  repository_name = review_request.repository.name
  if repository_name != RDIO_REPOSITORY:
    logging.info("Not hitting the jenkins web hook for repository %s" % (repository_name,))
    return

  if not review_request.revision:
    logging.info("Not hitting the jenkins web hook for review request %i: no revision info." % (review_request.id,))
    return

  try:
    raw_diff = get_raw_diff_str_from_review_request(review_request)
  except Exception as e:
    logging.error("Failed to get the raw diff for review request %i: %s" % (review_request.id, e), exc_info=1)
    return
    
  jenkins_params = {
      'revision': review_request.revision,
      'raw_patch': raw_diff,
  }
  try:
    resp = urllib.urlopen(settings.NEW_REVIEW_REQUEST_WEB_HOOK,
                          data=urllib.urlencode(jenkins_params)).read()
  except urllib2.HTTPError:
    logging.error("Failed to ping the jenkins endpoint for review request %i" % (review_request.id,))
  else:
    logging.info("Successfully hit the jenkins endpoint for review request %i.Response:\n%s" % (review_request.id, resp))


def connect_signals():
  review_request_published.connect(review_request_published_cb, sender=ReviewRequest)

def get_raw_diff_str_from_review_request(review_request):
  diffset = review_request.diffset_history.diffsets.order_by('-id')[0]
  tool = review_request.repository.get_scmtool()
  return tool.get_parser('').raw_diff(diffset)


