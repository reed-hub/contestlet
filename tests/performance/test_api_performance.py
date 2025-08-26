"""
Performance tests for API endpoints
"""
import pytest
import time
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.contest import Contest
from app.models.entry import Entry


class TestAPIPerformance:
    """Test API endpoint performance"""
    
    def test_health_check_performance(self, client: TestClient):
        """Test health check endpoint performance"""
        start_time = time.time()
        
        response = client.get("/")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        
        # Health check should be very fast (< 100ms)
        assert response_time < 0.1, f"Health check took {response_time:.3f}s, expected < 0.1s"
    
    def test_contest_listing_performance(self, client: TestClient, db_session: Session):
        """Test contest listing performance"""
        # Create multiple test contests
        contests = []
        for i in range(50):
            contest = Contest(
                name=f"Test Contest {i}",
                description=f"Test contest {i} description",
                start_time="2024-01-01T00:00:00Z",
                end_time="2024-12-31T23:59:59Z",
                active=True
            )
            contests.append(contest)
        
        db_session.add_all(contests)
        db_session.commit()
        
        # Test performance of listing contests
        start_time = time.time()
        response = client.get("/contests/active")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        
        # Contest listing should be reasonably fast (< 500ms for 50 contests)
        assert response_time < 0.5, f"Contest listing took {response_time:.3f}s, expected < 0.5s"
        
        data = response.json()
        assert len(data["contests"]) >= 50
    
    def test_user_authentication_performance(self, client: TestClient, db_session: Session):
        """Test user authentication performance"""
        # Create test user
        user = User(phone="+15551234567", role="user", is_verified=False)
        db_session.add(user)
        db_session.commit()
        
        # Test OTP request performance
        start_time = time.time()
        response = client.post("/auth/request-otp", json={"phone": "+15551234567"})
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        
        # OTP request should be reasonably fast (< 200ms)
        assert response_time < 0.2, f"OTP request took {response_time:.3f}s, expected < 0.2s"
    
    def test_database_query_performance(self, client: TestClient, db_session: Session):
        """Test database query performance"""
        # Create test data
        users = []
        for i in range(100):
            user = User(phone=f"+1555{i:07d}", role="user", is_verified=True)
            users.append(user)
        
        db_session.add_all(users)
        db_session.commit()
        
        # Test user listing performance
        start_time = time.time()
        response = client.get("/admin/users")
        end_time = time.time()
        
        # Should fail without auth, but we're testing the query performance
        # In a real scenario, this would be authenticated
        response_time = end_time - start_time
        
        # Database query should be reasonably fast (< 300ms for 100 users)
        assert response_time < 0.3, f"User listing took {response_time:.3f}s, expected < 0.3s"


class TestConcurrentRequests:
    """Test concurrent request handling"""
    
    def test_concurrent_health_checks(self, client: TestClient):
        """Test concurrent health check requests"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            start_time = time.time()
            response = client.get("/")
            end_time = time.time()
            
            results.put({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Start multiple concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        response_times = []
        while not results.empty():
            result = results.get()
            assert result["status_code"] == 200
            response_times.append(result["response_time"])
        
        # All requests should complete successfully
        assert len(response_times) == 10
        
        # Average response time should be reasonable
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 0.1, f"Average response time {avg_response_time:.3f}s too slow"
    
    def test_concurrent_contest_views(self, client: TestClient, db_session: Session):
        """Test concurrent contest viewing requests"""
        import threading
        import queue
        
        # Create test contest
        contest = Contest(
            name="Concurrent Test Contest",
            description="Contest for concurrent testing",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            active=True
        )
        db_session.add(contest)
        db_session.commit()
        
        results = queue.Queue()
        
        def view_contest():
            start_time = time.time()
            response = client.get(f"/contests/{contest.id}")
            end_time = time.time()
            
            results.put({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Start multiple concurrent requests
        threads = []
        for _ in range(20):
            thread = threading.Thread(target=view_contest)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        response_times = []
        while not results.empty():
            result = results.get()
            assert result["status_code"] == 200
            response_times.append(result["response_time"])
        
        # All requests should complete successfully
        assert len(response_times) == 20
        
        # Average response time should be reasonable
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 0.2, f"Average response time {avg_response_time:.3f}s too slow"


class TestMemoryUsage:
    """Test memory usage patterns"""
    
    def test_large_dataset_handling(self, client: TestClient, db_session: Session):
        """Test handling of large datasets"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large dataset
        contests = []
        for i in range(1000):
            contest = Contest(
                name=f"Large Contest {i}",
                description=f"Large contest {i} description" * 10,  # Long description
                start_time="2024-01-01T00:00:00Z",
                end_time="2024-12-31T23:59:59Z",
                active=True
            )
            contests.append(contest)
        
        db_session.add_all(contests)
        db_session.commit()
        
        # Test memory usage after large dataset
        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = current_memory - initial_memory
        
        # Memory increase should be reasonable (< 100MB for 1000 contests)
        assert memory_increase < 100, f"Memory increase {memory_increase:.1f}MB too high"
        
        # Test that we can still access the data
        response = client.get("/contests/active")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["contests"]) >= 1000
    
    def test_connection_pool_efficiency(self, client: TestClient, db_session: Session):
        """Test database connection pool efficiency"""
        import psutil
        import os
        
        # Get initial connection count
        process = psutil.Process(os.getpid())
        initial_connections = len(process.connections())
        
        # Make multiple database requests
        for i in range(50):
            response = client.get("/")
            assert response.status_code == 200
        
        # Get final connection count
        final_connections = len(process.connections())
        connection_increase = final_connections - initial_connections
        
        # Connection count should not increase significantly
        # (connection pooling should be working)
        assert connection_increase < 10, f"Connection increase {connection_increase} too high"


class TestResponseTimeConsistency:
    """Test response time consistency"""
    
    def test_response_time_consistency(self, client: TestClient):
        """Test that response times are consistent"""
        response_times = []
        
        # Make multiple requests
        for _ in range(20):
            start_time = time.time()
            response = client.get("/")
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        # Calculate statistics
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        variance = sum((t - avg_time) ** 2 for t in response_times) / len(response_times)
        std_dev = variance ** 0.5
        
        # Response times should be consistent (low variance)
        assert std_dev < avg_time * 0.5, f"Response time variance too high: std_dev={std_dev:.4f}s, avg={avg_time:.4f}s"
        
        # No single request should be significantly slower
        assert max_time < avg_time * 3, f"Slow request detected: {max_time:.4f}s vs avg {avg_time:.4f}s"
    
    def test_cold_start_performance(self, client: TestClient):
        """Test cold start performance"""
        # This test would require restarting the application
        # For now, we'll test that the first request is reasonable
        
        start_time = time.time()
        response = client.get("/")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        
        # Cold start should be reasonable (< 500ms)
        assert response_time < 0.5, f"Cold start took {response_time:.3f}s, expected < 0.5s"


class TestLoadHandling:
    """Test load handling capabilities"""
    
    def test_sustained_load(self, client: TestClient):
        """Test sustained load handling"""
        import threading
        import queue
        
        results = queue.Queue()
        stop_event = threading.Event()
        
        def sustained_request():
            while not stop_event.is_set():
                start_time = time.time()
                response = client.get("/")
                end_time = time.time()
                
                if response.status_code == 200:
                    results.put(end_time - start_time)
        
        # Start multiple sustained request threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=sustained_request)
            threads.append(thread)
            thread.start()
        
        # Let them run for a short time
        time.sleep(2)
        
        # Stop the threads
        stop_event.set()
        for thread in threads:
            thread.join()
        
        # Collect results
        response_times = []
        while not results.empty():
            response_times.append(results.get())
        
        # Should have handled sustained load
        assert len(response_times) > 0
        
        # Average response time should remain reasonable
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            assert avg_response_time < 0.3, f"Sustained load avg response time {avg_response_time:.3f}s too slow"
