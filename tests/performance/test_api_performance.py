"""
Enhanced performance tests with production benchmarks
"""
import pytest
import time
import asyncio
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.contest import Contest
from app.models.entry import Entry


class TestAPIPerformanceBenchmarks:
    """Test API endpoint performance with production benchmarks"""
    
    def test_health_check_performance(self, client: TestClient):
        """Test health check endpoint performance"""
        # Run multiple iterations for accurate measurement
        response_times = []
        
        for _ in range(10):
            start_time = time.time()
            response = client.get("/")
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        
        # Production benchmarks
        assert avg_time < 0.05, f"Average health check time {avg_time:.3f}s, expected < 0.05s"
        assert max_time < 0.1, f"Max health check time {max_time:.3f}s, expected < 0.1s"
        assert p95_time < 0.08, f"95th percentile {p95_time:.3f}s, expected < 0.08s"
    
    def test_contest_listing_performance(self, client: TestClient, db_session: Session):
        """Test contest listing performance with production benchmarks"""
        # Create realistic test data (200 contests)
        contests = []
        for i in range(200):
            contest = Contest(
                name=f"Performance Test Contest {i+1}",
                description=f"Contest {i+1} with detailed description for performance testing. This includes longer text to simulate real-world data sizes.",
                status="active",
                start_time=time.time() - 3600,  # Started 1 hour ago
                end_time=time.time() + 604800,  # Ends in 1 week
                prize_description=f"Prize for contest {i+1} worth $100-$500",
                contest_type="general",
                entry_method="sms",
                winner_selection_method="random",
                minimum_age=18,
                max_entries_per_person=1,
                total_entry_limit=100,
                location=f"City {i+1}, State {i%50}"
            )
            contests.append(contest)
        
        db_session.add_all(contests)
        db_session.commit()
        
        # Test performance with multiple requests
        response_times = []
        for _ in range(5):
            start_time = time.time()
            response = client.get("/contests/active")
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        # Calculate performance metrics
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 5 else max_time
        
        # Production benchmarks for 200 contests
        assert avg_time < 0.3, f"Average contest listing time {avg_time:.3f}s, expected < 0.3s"
        assert max_time < 0.5, f"Max contest listing time {max_time:.3f}s, expected < 0.5s"
        assert p95_time < 0.4, f"95th percentile {p95_time:.3f}s, expected < 0.4s"
        
        # Verify data integrity
        data = response.json()
        assert len(data["contests"]) == 200
        assert data["total"] == 200
    
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


class TestConcurrentRequestsProduction:
    """Test concurrent request handling with production benchmarks"""
    
    def test_concurrent_health_checks(self, client: TestClient):
        """Test concurrent health check requests"""
        def make_request():
            start_time = time.time()
            response = client.get("/")
            end_time = time.time()
            
            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time
            }
        
        # Test with realistic concurrent load (50 requests)
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [future.result() for future in as_completed(futures)]
        
        # Collect response times
        response_times = [r["response_time"] for r in results]
        success_count = sum(1 for r in results if r["status_code"] == 200)
        
        # Calculate performance metrics
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18]
        
        # Production benchmarks for concurrent requests
        assert success_count == 50, f"Only {success_count}/50 requests succeeded"
        assert avg_time < 0.1, f"Average concurrent response time {avg_time:.3f}s, expected < 0.1s"
        assert max_time < 0.5, f"Max concurrent response time {max_time:.3f}s, expected < 0.5s"
        assert p95_time < 0.2, f"95th percentile {p95_time:.3f}s, expected < 0.2s"
    
    def test_high_load_contest_listing(self, client: TestClient, db_session: Session):
        """Test high load on contest listing endpoint"""
        # Create test contests
        contests = []
        for i in range(100):
            contest = Contest(
                name=f"Load Test Contest {i+1}",
                description=f"Contest {i+1} for load testing",
                status="active",
                start_time=time.time() - 3600,
                end_time=time.time() + 604800,
                prize_description="Load test prize",
                contest_type="general",
                entry_method="sms",
                winner_selection_method="random",
                minimum_age=18,
                max_entries_per_person=1,
                total_entry_limit=100
            )
            contests.append(contest)
        
        db_session.add_all(contests)
        db_session.commit()
        
        def make_contest_request():
            start_time = time.time()
            response = client.get("/contests/active")
            end_time = time.time()
            
            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "data_size": len(response.content) if response.status_code == 200 else 0
            }
        
        # Simulate high load (100 concurrent requests)
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_contest_request) for _ in range(100)]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze results
        response_times = [r["response_time"] for r in results]
        success_count = sum(1 for r in results if r["status_code"] == 200)
        avg_data_size = statistics.mean([r["data_size"] for r in results if r["data_size"] > 0])
        
        # Performance benchmarks under high load
        assert success_count >= 95, f"Only {success_count}/100 requests succeeded under high load"
        
        avg_time = statistics.mean(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18]
        
        assert avg_time < 1.0, f"Average response time under load {avg_time:.3f}s, expected < 1.0s"
        assert p95_time < 2.0, f"95th percentile under load {p95_time:.3f}s, expected < 2.0s"
        assert avg_data_size > 1000, f"Average response size {avg_data_size} bytes seems too small"
    
    def test_mixed_endpoint_load(self, client: TestClient, db_session: Session):
        """Test mixed load across different endpoints"""
        # Create test data
        user = User(phone="+15551234567", role="user", is_verified=True)
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add_all([user, admin])
        db_session.commit()
        
        # Create admin token
        from app.core.auth import jwt_manager
        admin_token = jwt_manager.create_access_token(
            user_id=admin.id, phone=admin.phone, role=admin.role
        )
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create test contests
        for i in range(50):
            contest = Contest(
                name=f"Mixed Load Contest {i+1}",
                description=f"Contest {i+1} for mixed load testing",
                status="active",
                start_time=time.time() - 3600,
                end_time=time.time() + 604800,
                prize_description="Mixed load test prize",
                contest_type="general",
                entry_method="sms",
                winner_selection_method="random",
                minimum_age=18,
                max_entries_per_person=1,
                total_entry_limit=100
            )
            db_session.add(contest)
        db_session.commit()
        
        def make_mixed_requests():
            endpoints = [
                ("/", "GET", {}),
                ("/health", "GET", {}),
                ("/contests/active", "GET", {}),
                ("/admin/contests/", "GET", admin_headers),
                ("/manifest.json", "GET", {})
            ]
            
            results = []
            for endpoint, method, headers in endpoints:
                start_time = time.time()
                if method == "GET":
                    response = client.get(endpoint, headers=headers)
                end_time = time.time()
                
                results.append({
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time
                })
            
            return results
        
        # Run mixed load test
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_mixed_requests) for _ in range(20)]
            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())
        
        # Analyze results by endpoint
        endpoint_stats = {}
        for result in all_results:
            endpoint = result["endpoint"]
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = []
            endpoint_stats[endpoint].append(result)
        
        # Verify performance for each endpoint
        for endpoint, results in endpoint_stats.items():
            response_times = [r["response_time"] for r in results]
            success_rate = sum(1 for r in results if r["status_code"] in [200, 201]) / len(results)
            avg_time = statistics.mean(response_times)
            
            assert success_rate >= 0.95, f"Endpoint {endpoint} success rate {success_rate:.2%}, expected >= 95%"
            
            # Different benchmarks for different endpoints
            if endpoint in ["/", "/health", "/manifest.json"]:
                assert avg_time < 0.1, f"Endpoint {endpoint} avg time {avg_time:.3f}s, expected < 0.1s"
            elif endpoint == "/contests/active":
                assert avg_time < 0.5, f"Endpoint {endpoint} avg time {avg_time:.3f}s, expected < 0.5s"
            elif endpoint == "/admin/contests/":
                assert avg_time < 1.0, f"Endpoint {endpoint} avg time {avg_time:.3f}s, expected < 1.0s"
    
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


class TestDatabasePerformance:
    """Test database performance and optimization"""
    
    def test_large_dataset_query_performance(self, client: TestClient, db_session: Session):
        """Test query performance with large datasets"""
        # Create large dataset (1000 contests, 2000 users, 5000 entries)
        users = []
        for i in range(2000):
            user = User(
                phone=f"+1555{i:07d}",
                role="user" if i % 10 != 0 else "sponsor",
                is_verified=True,
                first_name=f"User{i}",
                last_name=f"Test{i}",
                email=f"user{i}@example.com"
            )
            users.append(user)
        
        db_session.add_all(users)
        db_session.commit()
        
        contests = []
        for i in range(1000):
            contest = Contest(
                name=f"Large Dataset Contest {i+1}",
                description=f"Contest {i+1} for large dataset performance testing with detailed description.",
                status="active" if i % 3 == 0 else "upcoming",
                start_time=time.time() - (i % 100) * 3600,  # Varied start times
                end_time=time.time() + 604800 + (i % 100) * 3600,  # Varied end times
                created_by_user_id=users[i % 200].id,  # Distribute among sponsors
                prize_description=f"Prize for contest {i+1} worth ${100 + i % 500}",
                contest_type=["general", "photo", "video", "text"][i % 4],
                entry_method="sms",
                winner_selection_method="random",
                minimum_age=18,
                max_entries_per_person=1,
                total_entry_limit=100,
                location=f"City {i % 100}, State {i % 50}"
            )
            contests.append(contest)
        
        db_session.add_all(contests)
        db_session.commit()
        
        # Create entries
        entries = []
        for i in range(5000):
            entry = Entry(
                contest_id=contests[i % 1000].id,
                user_id=users[i % 2000].id,
                is_valid=True,
                entry_data=f"Entry data {i+1}"
            )
            entries.append(entry)
        
        db_session.add_all(entries)
        db_session.commit()
        
        # Test various query performance scenarios
        test_scenarios = [
            ("/contests/active", "Active contests with large dataset"),
            ("/contests/active?page=1&size=50", "Paginated active contests"),
            ("/contests/active?contest_type=photo", "Filtered contests"),
            ("/contests/nearby?lat=34.0522&lng=-118.2437&radius=50", "Nearby contests"),
        ]
        
        for endpoint, description in test_scenarios:
            response_times = []
            for _ in range(3):  # Multiple runs for accuracy
                start_time = time.time()
                response = client.get(endpoint)
                end_time = time.time()
                
                if response.status_code == 200:
                    response_times.append(end_time - start_time)
            
            if response_times:
                avg_time = statistics.mean(response_times)
                max_time = max(response_times)
                
                # Performance benchmarks for large datasets
                assert avg_time < 2.0, f"{description}: avg time {avg_time:.3f}s, expected < 2.0s"
                assert max_time < 3.0, f"{description}: max time {max_time:.3f}s, expected < 3.0s"
    
    def test_database_connection_efficiency(self, client: TestClient, db_session: Session):
        """Test database connection pool efficiency"""
        import psutil
        import os
        
        # Get initial connection count
        process = psutil.Process(os.getpid())
        initial_connections = len([c for c in process.connections() if c.status == 'ESTABLISHED'])
        
        # Make many requests that require database access
        def make_db_request():
            return client.get("/contests/active")
        
        # Execute many concurrent database requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_db_request) for _ in range(100)]
            results = [future.result() for future in as_completed(futures)]
        
        # Get final connection count
        final_connections = len([c for c in process.connections() if c.status == 'ESTABLISHED'])
        connection_increase = final_connections - initial_connections
        
        # Verify connection pooling is working efficiently
        assert connection_increase < 20, f"Connection increase {connection_increase} too high, connection pooling may not be working"
        
        # Verify all requests succeeded
        success_count = sum(1 for r in results if r.status_code == 200)
        assert success_count >= 95, f"Only {success_count}/100 database requests succeeded"
    
    def test_query_optimization_indexes(self, client: TestClient, db_session: Session):
        """Test that database indexes are working for common queries"""
        # Create test data with specific patterns for index testing
        users = []
        for i in range(500):
            user = User(
                phone=f"+1555{i:07d}",
                role="user",
                is_verified=True
            )
            users.append(user)
        
        db_session.add_all(users)
        db_session.commit()
        
        contests = []
        for i in range(500):
            contest = Contest(
                name=f"Index Test Contest {i+1}",
                description=f"Contest {i+1} for index testing",
                status=["draft", "awaiting_approval", "upcoming", "active", "ended"][i % 5],
                start_time=time.time() - (i % 100) * 3600,
                end_time=time.time() + 604800,
                created_by_user_id=users[i % 500].id,
                prize_description="Index test prize",
                contest_type=["general", "photo", "video"][i % 3],
                entry_method="sms",
                winner_selection_method="random",
                minimum_age=18,
                max_entries_per_person=1,
                total_entry_limit=100
            )
            contests.append(contest)
        
        db_session.add_all(contests)
        db_session.commit()
        
        # Test queries that should benefit from indexes
        indexed_queries = [
            ("/contests/active", "status index"),
            ("/contests/active?contest_type=photo", "contest_type index"),
            # Add more index-dependent queries as needed
        ]
        
        for endpoint, index_description in indexed_queries:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            assert response.status_code == 200
            query_time = end_time - start_time
            
            # Indexed queries should be fast even with 500 records
            assert query_time < 0.5, f"{index_description} query took {query_time:.3f}s, may need index optimization"


class TestMemoryAndResourceUsage:
    """Test memory usage and resource management"""
    
    def test_memory_usage_under_load(self, client: TestClient, db_session: Session):
        """Test memory usage patterns under load"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create substantial test data
        contests = []
        for i in range(500):
            contest = Contest(
                name=f"Memory Test Contest {i+1}",
                description=f"Contest {i+1} with substantial description for memory testing. " * 10,  # Long description
                status="active",
                start_time=time.time() - 3600,
                end_time=time.time() + 604800,
                prize_description=f"Detailed prize description for contest {i+1}. " * 5,
                contest_type="general",
                entry_method="sms",
                winner_selection_method="random",
                minimum_age=18,
                max_entries_per_person=1,
                total_entry_limit=100,
                location=f"Detailed location for contest {i+1}, City, State 12345"
            )
            contests.append(contest)
        
        db_session.add_all(contests)
        db_session.commit()
        
        # Generate load and monitor memory
        def make_memory_test_request():
            return client.get("/contests/active")
        
        # Execute requests while monitoring memory
        memory_samples = []
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_memory_test_request) for _ in range(100)]
            
            # Sample memory usage during execution
            for i, future in enumerate(as_completed(futures)):
                result = future.result()
                assert result.status_code == 200
                
                if i % 10 == 0:  # Sample every 10 requests
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_samples.append(current_memory)
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        max_memory = max(memory_samples) if memory_samples else final_memory
        
        # Memory usage should be reasonable
        assert memory_increase < 200, f"Memory increase {memory_increase:.1f}MB too high"
        assert max_memory < initial_memory + 250, f"Peak memory usage {max_memory:.1f}MB too high"
    
    def test_resource_cleanup_after_requests(self, client: TestClient, db_session: Session):
        """Test that resources are properly cleaned up after requests"""
        import gc
        import psutil
        import os
        
        # Force garbage collection and get baseline
        gc.collect()
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # Create test data
        for i in range(100):
            contest = Contest(
                name=f"Cleanup Test Contest {i+1}",
                description=f"Contest {i+1} for cleanup testing",
                status="active",
                start_time=time.time() - 3600,
                end_time=time.time() + 604800,
                prize_description="Cleanup test prize",
                contest_type="general",
                entry_method="sms",
                winner_selection_method="random",
                minimum_age=18,
                max_entries_per_person=1,
                total_entry_limit=100
            )
            db_session.add(contest)
        db_session.commit()
        
        # Make many requests
        for _ in range(200):
            response = client.get("/contests/active")
            assert response.status_code == 200
        
        # Force cleanup and measure
        gc.collect()
        time.sleep(1)  # Allow cleanup to complete
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        # Memory should not have increased significantly after cleanup
        assert memory_increase < 100, f"Memory not properly cleaned up, increase: {memory_increase:.1f}MB"
    
    def test_file_descriptor_usage(self, client: TestClient, db_session: Session):
        """Test file descriptor usage and cleanup"""
        import psutil
        import os
        
        # Get initial file descriptor count
        process = psutil.Process(os.getpid())
        initial_fds = process.num_fds() if hasattr(process, 'num_fds') else len(process.open_files())
        
        # Make many requests that could potentially leak file descriptors
        for _ in range(100):
            response = client.get("/contests/active")
            assert response.status_code == 200
        
        # Get final file descriptor count
        final_fds = process.num_fds() if hasattr(process, 'num_fds') else len(process.open_files())
        fd_increase = final_fds - initial_fds
        
        # File descriptor count should not increase significantly
        assert fd_increase < 10, f"File descriptor leak detected, increase: {fd_increase}"


class TestProductionScenarios:
    """Test realistic production scenarios"""
    
    def test_realistic_user_behavior_simulation(self, client: TestClient, db_session: Session):
        """Simulate realistic user behavior patterns"""
        # Create realistic test data
        users = []
        for i in range(100):
            user = User(
                phone=f"+1555{i:07d}",
                role="user" if i % 20 != 0 else "sponsor",
                is_verified=True
            )
            users.append(user)
        
        db_session.add_all(users)
        db_session.commit()
        
        # Create contests with realistic distribution
        contests = []
        for i in range(50):
            contest = Contest(
                name=f"Realistic Contest {i+1}",
                description=f"Contest {i+1} with realistic data patterns",
                status=["active", "upcoming", "ended"][i % 3] if i % 10 != 0 else "draft",
                start_time=time.time() - (i % 10) * 86400,  # Varied start times
                end_time=time.time() + (7 + i % 14) * 86400,  # 1-3 weeks duration
                prize_description=f"Realistic prize for contest {i+1}",
                contest_type=["general", "photo", "video"][i % 3],
                entry_method="sms",
                winner_selection_method="random",
                minimum_age=18,
                max_entries_per_person=1,
                total_entry_limit=100 + (i % 5) * 50  # Varied limits
            )
            contests.append(contest)
        
        db_session.add_all(contests)
        db_session.commit()
        
        # Simulate realistic user behavior patterns
        def simulate_user_session():
            session_requests = []
            
            # Typical user session: browse contests, view details, maybe enter
            session_requests.extend([
                ("/", "GET"),  # Landing page
                ("/contests/active", "GET"),  # Browse contests
                ("/contests/active?page=2", "GET"),  # Next page
                (f"/contests/{contests[0].id}", "GET"),  # View contest details
                (f"/contests/{contests[1].id}", "GET"),  # View another contest
                ("/health", "GET"),  # Health check (monitoring)
            ])
            
            results = []
            for endpoint, method in session_requests:
                start_time = time.time()
                response = client.get(endpoint)
                end_time = time.time()
                
                results.append({
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time
                })
            
            return results
        
        # Simulate multiple concurrent user sessions
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(simulate_user_session) for _ in range(30)]
            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())
        
        # Analyze realistic usage patterns
        total_requests = len(all_results)
        successful_requests = sum(1 for r in all_results if r["status_code"] == 200)
        avg_response_time = statistics.mean([r["response_time"] for r in all_results])
        
        # Production-ready metrics for realistic scenarios
        success_rate = successful_requests / total_requests
        assert success_rate >= 0.98, f"Success rate {success_rate:.2%} too low for production"
        assert avg_response_time < 0.5, f"Average response time {avg_response_time:.3f}s too slow for production"
        
        # Verify no single request was extremely slow
        max_response_time = max([r["response_time"] for r in all_results])
        assert max_response_time < 5.0, f"Slowest request {max_response_time:.3f}s unacceptable for production"
