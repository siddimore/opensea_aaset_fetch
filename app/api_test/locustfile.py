from locust import HttpUser, task, between

class WebsiteTestUser(HttpUser):
  wait_time = between(0.5, 3.0)

  def on_start(self):
      """ on_start is called when a Locust start before any task is scheduled """
      pass

  def on_stop(self):
      """ on_stop is called when the TaskSet is stopping """
      pass

  # @task(1)
  # def index(self):
  #   self.client.get("/")

  @task(1)
  def fetch_tokens(self):
      self.client.get("/api/fetchTokens")