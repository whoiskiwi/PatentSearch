"""
Locust performance testing for Thinkstruct Patent Search API.

Run with:
    cd tests/performance
    locust -f locustfile.py --host=http://localhost:5000

Then open http://localhost:8089 to configure and start tests.
Target: 100 concurrent users with P95 response time < 2 seconds.
"""

import random
from locust import HttpUser, task, between, events
from test_data import (
    get_random_invalidity_query,
    get_random_infringement_query,
    get_random_patentability_query,
    get_random_history_entry,
)


class PatentSearchUser(HttpUser):
    """Simulates a regular user performing patent searches."""

    # Wait 1-3 seconds between tasks
    wait_time = between(1, 3)

    def on_start(self):
        """Called when a simulated user starts."""
        # Check API health
        self.client.get("/api/health", name="health_check")

    @task(3)
    def search_invalidity(self):
        """Search for prior art (invalidity analysis) - most common search."""
        query = get_random_invalidity_query()
        with self.client.post(
            "/api/search/invalidity",
            json=query,
            name="search_invalidity",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    response.success()
                else:
                    response.failure("No results field in response")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(2)
    def search_patentability(self):
        """Search for patentability assessment."""
        query = get_random_patentability_query()
        with self.client.post(
            "/api/search/patentability",
            json=query,
            name="search_patentability",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    response.success()
                else:
                    response.failure("No results field in response")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def search_infringement(self):
        """Search for potential infringement."""
        query = get_random_infringement_query()
        with self.client.post(
            "/api/search/infringement",
            json=query,
            name="search_infringement",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    response.success()
                else:
                    response.failure("No results field in response")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def get_stats(self):
        """Get API statistics."""
        self.client.get("/api/stats", name="get_stats")


class AuthenticatedUser(HttpUser):
    """Simulates an authenticated user who also saves search history."""

    wait_time = between(1, 3)

    # Simulated JWT token (won't be valid, but tests the endpoint structure)
    token = None

    def on_start(self):
        """Called when a simulated user starts."""
        # Check auth status (will show as not authenticated)
        self.client.get("/api/auth/status", name="auth_status")

    @task(3)
    def search_and_save_history(self):
        """Perform a search and attempt to save to history."""
        # First, do a search
        query = get_random_invalidity_query()
        with self.client.post(
            "/api/search/invalidity",
            json=query,
            name="auth_search_invalidity",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()

                # Try to save to history (will fail with 401, but tests the endpoint)
                history_entry = get_random_history_entry()
                with self.client.post(
                    "/api/history",
                    json=history_entry,
                    name="save_history",
                    catch_response=True,
                ) as hist_response:
                    # Expected to fail with 401 (not authenticated)
                    if hist_response.status_code in [200, 201, 401]:
                        hist_response.success()
                    else:
                        hist_response.failure(f"Unexpected status: {hist_response.status_code}")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def get_history(self):
        """Attempt to get search history."""
        with self.client.get(
            "/api/history",
            name="get_history",
            catch_response=True,
        ) as response:
            # Expected to fail with 401 (not authenticated)
            if response.status_code in [200, 401]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class MixedUser(HttpUser):
    """
    Simulates a mix of authenticated and unauthenticated user behavior.
    This is the recommended user class for realistic load testing.
    """

    wait_time = between(1, 5)

    @task(5)
    def search_invalidity(self):
        """Most common: invalidity search."""
        query = get_random_invalidity_query()
        self.client.post(
            "/api/search/invalidity",
            json=query,
            name="mixed_invalidity",
        )

    @task(3)
    def search_patentability(self):
        """Common: patentability search."""
        query = get_random_patentability_query()
        self.client.post(
            "/api/search/patentability",
            json=query,
            name="mixed_patentability",
        )

    @task(2)
    def search_infringement(self):
        """Less common: infringement search."""
        query = get_random_infringement_query()
        self.client.post(
            "/api/search/infringement",
            json=query,
            name="mixed_infringement",
        )

    @task(2)
    def get_stats(self):
        """Frequent: get stats (often called on page load)."""
        self.client.get("/api/stats", name="mixed_stats")

    @task(1)
    def check_health(self):
        """Periodic: health check."""
        self.client.get("/api/health", name="mixed_health")

    @task(1)
    def check_auth_status(self):
        """On page load: check auth status."""
        self.client.get("/api/auth/status", name="mixed_auth_status")


# Event handlers for custom logging
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log slow requests (> 2 seconds)."""
    if response_time > 2000:  # 2 seconds in milliseconds
        print(f"SLOW REQUEST: {name} took {response_time}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("=" * 60)
    print("Starting Thinkstruct Patent Search Performance Test")
    print("Target: 100 concurrent users, P95 < 2 seconds")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    print("=" * 60)
    print("Performance Test Complete")
    print("=" * 60)
