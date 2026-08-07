"""
Simple test script to verify the ticket app is working locally.
Run this after starting app.py to test all endpoints.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n1. Testing health check...")
    response = requests.get(f"{BASE_URL}/healthz")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200
    print("   ✓ Health check passed")

def test_create_ticket():
    """Test creating a ticket"""
    print("\n2. Creating a new ticket...")
    ticket_data = {
        "title": "Test ticket - Database connection issue",
        "status": "open"
    }
    response = requests.post(f"{BASE_URL}/tickets", json=ticket_data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 201
    ticket = response.json()
    print("   ✓ Ticket created successfully")
    return ticket["ticket_id"]

def test_list_tickets():
    """Test listing tickets"""
    print("\n3. Listing all tickets...")
    response = requests.get(f"{BASE_URL}/tickets")
    print(f"   Status: {response.status_code}")
    tickets = response.json()
    print(f"   Found {len(tickets)} ticket(s)")
    if tickets:
        print(f"   Latest: {tickets[0]['title']}")
    assert response.status_code == 200
    print("   ✓ List tickets passed")

def test_add_message(ticket_id):
    """Test adding a message to a ticket"""
    print(f"\n4. Adding message to ticket {ticket_id}...")
    message_data = {
        "message_text": "This is a test message. I am investigating the issue."
    }
    response = requests.post(f"{BASE_URL}/tickets/{ticket_id}/messages", json=message_data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 201
    print("   ✓ Message added successfully")
    return response.json()["message_id"]

def test_get_ticket(ticket_id):
    """Test getting a specific ticket with messages"""
    print(f"\n5. Getting ticket {ticket_id} with messages...")
    response = requests.get(f"{BASE_URL}/tickets/{ticket_id}")
    print(f"   Status: {response.status_code}")
    ticket = response.json()
    print(f"   Title: {ticket['title']}")
    print(f"   Status: {ticket['status']}")
    print(f"   Messages: {len(ticket.get('messages', []))}")
    assert response.status_code == 200
    print("   ✓ Get ticket passed")

def test_update_ticket(ticket_id):
    """Test updating a ticket"""
    print(f"\n6. Updating ticket {ticket_id} status...")
    update_data = {"status": "in_progress"}
    response = requests.put(f"{BASE_URL}/tickets/{ticket_id}", json=update_data)
    print(f"   Status: {response.status_code}")
    ticket = response.json()
    print(f"   New status: {ticket['status']}")
    assert response.status_code == 200
    assert ticket['status'] == 'in_progress'
    print("   ✓ Update ticket passed")

if __name__ == "__main__":
    print("=" * 60)
    print("TICKET APP LOCAL TEST")
    print("=" * 60)
    print("\nMake sure the app is running on http://localhost:8000")
    print("Start it with: python app.py")
    print("=" * 60)
    
    try:
        test_health()
        ticket_id = test_create_ticket()
        test_list_tickets()
        message_id = test_add_message(ticket_id)
        test_get_ticket(ticket_id)
        test_update_ticket(ticket_id)
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print(f"\nYour test ticket ID: {ticket_id}")
        print(f"View it at: http://localhost:8000/tickets/{ticket_id}")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to the app.")
        print("Make sure the app is running: python app.py")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
