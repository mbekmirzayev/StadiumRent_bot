import requests

from config import BASE_URL


class APIClient:
    def __init__(self):
        self.base_url = BASE_URL

    def register_user(self, phone, telegram_id, first_name):
        url = f"{self.base_url}/user/create"
        data = {
            "phone": str(phone),
            "telegram_id": telegram_id,
            "first_name": first_name,
            # 'last_name': last_name,
            "password": f"pass_{telegram_id}"
        }

        response = requests.post(url, json=data)

        if response.status_code != 201:
            print(f"Status: {response.status_code}")
            print(f"Body: {response.json()}")
            print(f"---------------------------")

        return response.status_code, response.json()

    def check_user_exists(self, telegram_id):
        url = f"{self.base_url}/user/check/{telegram_id}/"
        try:
            response = requests.get(url)
            return response.status_code == 200
        except Exception:
            return False

    def get_token(self, telegram_id):
        url = f"{self.base_url}/user/login-telegram/"
        response = requests.post(url, json={"telegram_id": telegram_id})
        if response.status_code == 200:
            return response.json()
        return None

    def get_stadiums(self, lat=None, lon=None, date=None, start_time=None, end_time=None):
        url = f"{self.base_url}/stadium/"
        params = {}
        if lat and lon: params.update({"lat": lat, "lon": lon})
        if date and start_time and end_time:
            params.update({"date": date, "start_time": start_time, "end_time": end_time})

        response = requests.get(url, params=params)
        return response.json() if response.status_code == 200 else []

    def get_stadium_detail(self, stadium_id):
        url = f"{self.base_url}/stadium/{stadium_id}/"
        try:
            response = requests.get(url)
            print(f"API Request to: {url} | Status: {response.status_code}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Backendga bog'lanishda xato: {e}")
        return None

    def create_booking(self, token, data):
        url = f"{self.base_url}/bookings/"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(url, json=data, headers=headers)
        return response.status_code, response.json()

    def get_my_bookings(self, token):
        url = f"{self.base_url}/bookings/"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return []

    def cancel_booking(self, token, booking_id):
        url = f"{self.base_url}/bookings/{booking_id}/cancel/"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(url, headers=headers)
        return response.status_code

    def get_nearby_stadiums(self, lat, lon, page=1):
        url = f"{self.base_url}/stadium/?lat={lat}&lon={lon}&page={page}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None