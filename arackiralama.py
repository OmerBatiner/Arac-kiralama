import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, \
    QMessageBox, QListWidget
from PyQt6.QtCore import QTimer
from pymongo import MongoClient
from datetime import datetime, timedelta


class CarRentalApp(QWidget):
    def __init__(self):
        super().__init__()

        self.admin_page = None
        self.rental_page = None
        self.login_button = None
        self.signin_button = None
        self.show_password_checkbox = None
        self.password_input = None
        self.password_label = None
        self.username_input = None
        self.username_label = None
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client["car_rental"]
        self.users_collection = self.db["users"]
        self.vehicles_collection = self.db["vehicles"]

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Car Rental App')
        self.setGeometry(100, 100, 400, 200)

        self.username_label = QLabel('Username:')
        self.username_input = QLineEdit(self)

        self.password_label = QLabel('Password:')
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.show_password_checkbox = QPushButton('Show Password', self)
        self.show_password_checkbox.setCheckable(True)
        self.show_password_checkbox.clicked.connect(self.toggle_password_visibility)

        self.signin_button = QPushButton('Sign In', self)
        self.signin_button.clicked.connect(self.signin)

        self.login_button = QPushButton('Log In', self)
        self.login_button.clicked.connect(self.login)

        layout = QVBoxLayout()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.show_password_checkbox)
        layout.addWidget(self.signin_button)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

        self.show()

    def toggle_password_visibility(self):
        if self.show_password_checkbox.isChecked():
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

    def signin(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, 'Error', 'Username and password cannot be empty.')
        else:
            existing_user = self.users_collection.find_one({'username': username})
            if existing_user:
                QMessageBox.warning(self, 'Error', 'This username is already taken. Please choose another username.')
            else:
                user_data = {'username': username, 'password': password}
                self.users_collection.insert_one(user_data)

                QMessageBox.information(self, 'Success', 'Sign In successful!')

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        user = self.users_collection.find_one({'username': username, 'password': password})

        if user:
            if username == 'admin' and password == 'admin123':
                self.show_admin_page()
            else:
                QMessageBox.information(self, 'Success', 'Login successful!')
                self.show_rental_page(user['_id'])
        else:
            QMessageBox.warning(self, 'Error', 'Invalid username or password')

    def show_rental_page(self, user_id):
        self.rental_page = RentalPage(user_id, self)
        self.rental_page.show()
        self.hide()

        # Ekran gÃ¼ncellemesini kontrol et
        QApplication.processEvents()

    def show_admin_page(self):
        self.admin_page = AdminPage(self)
        self.admin_page.show()
        self.hide()

    def exit_to_login(self):
        self.show()
        self.admin_page.close()


class RentalPage(QWidget):
    def __init__(self, user_id, main_window):
        super().__init__()

        self.exit_to_login_button = None
        self.rental_date_input = None
        self.rent_button = None
        self.rental_date_label = None
        self.vehicle_list = None
        self.vehicle_list_label = None
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client["car_rental"]
        self.vehicles_collection = self.db["vehicles"]
        self.user_id = user_id
        self.main_window = main_window

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Car Rental Page')
        self.setGeometry(100, 100, 400, 300)

        date_format_label = QLabel('Enter rental end date (YYYY-MM-DD):')

        self.vehicle_list_label = QLabel('Available Vehicles:')
        self.vehicle_list = QListWidget(self)

        self.rental_date_label = QLabel('Rental End Date:')
        self.rental_date_input = QLineEdit(self)

        self.rent_button = QPushButton('Rent Vehicle', self)
        self.rent_button.clicked.connect(self.rent_vehicle)

        self.exit_to_login_button = QPushButton('Exit to Login', self)
        self.exit_to_login_button.clicked.connect(self.exit_to_login)

        layout = QVBoxLayout()
        layout.addWidget(date_format_label)
        layout.addWidget(self.vehicle_list_label)
        layout.addWidget(self.vehicle_list)
        layout.addWidget(self.rental_date_label)
        layout.addWidget(self.rental_date_input)
        layout.addWidget(self.rent_button)
        layout.addWidget(self.exit_to_login_button)

        self.load_available_vehicles()

        self.setLayout(layout)
        self.show()

    def load_available_vehicles(self):
        self.vehicle_list.clear()
        available_vehicles = self.vehicles_collection.find({'available': True})

        for vehicle in available_vehicles:
            item_text = f"{vehicle['brand']} {vehicle['model']} ({vehicle['year']}) - GÃ¼nlÃ¼k Fiyat: {vehicle.get('kiralama_fiyati', 0.00)} TL"
            self.vehicle_list.addItem(item_text)

    def rent_vehicle(self):
        rental_end_date_str = self.rental_date_input.text().strip()

        if not rental_end_date_str:
            QMessageBox.warning(self, 'Error', 'Rental end date cannot be empty.')
            return

        selected_item = self.vehicle_list.currentItem()

        if selected_item:
            selected_vehicle_text = selected_item.text()
            selected_vehicle_parts = selected_vehicle_text.split(' ')
            brand = selected_vehicle_parts[0]
            model = selected_vehicle_parts[1]
            year = selected_vehicle_parts[2][1:-1]

            rental_end_date = datetime.strptime(rental_end_date_str, "%Y-%m-%d")
            vehicle = self.vehicles_collection.find_one({'brand': brand, 'model': model, 'year': int(year)})

            if vehicle['available']:
                rental_end_time = rental_end_date + timedelta(days=1)
                renting_user_id = self.user_id

                self.vehicles_collection.update_one(
                    {'brand': brand, 'model': model, 'year': int(year)},
                    {'$set': {'available': False, 'rental_end_time': rental_end_time,
                              'kiralayan_kisi': renting_user_id}}
                )

                QMessageBox.information(self, 'Success', 'AraÃ§ baÅŸarÄ±yla kiralandÄ±!')
                self.load_available_vehicles()
            else:
                QMessageBox.warning(self, 'Error', 'SeÃ§ilen araÃ§ kiralanamaz.')
        else:
            QMessageBox.warning(self, 'Error', 'LÃ¼tfen bir araÃ§ seÃ§in.')

    def exit_to_login(self):
        self.main_window.show()
        self.close()


class AdminPage(QWidget):
    def __init__(self, main_window):
        super().__init__()

        self.update_datetime_timer = None
        self.not_delivered_button = None
        self.vehicle_list = None
        self.delivered_button = None
        self.vehicle_list_label = None
        self.current_datetime_label = None
        self.exit_to_login_button = None  # Yeni eklenen buton
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client["car_rental"]
        self.vehicles_collection = self.db["vehicles"]
        self.main_window = main_window

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Admin Page')
        self.setGeometry(100, 100, 600, 400)

        self.current_datetime_label = QLabel('GÃ¼ncel Tarih ve Saat:')
        self.vehicle_list_label = QLabel('TÃ¼m AraÃ§lar:')
        self.vehicle_list = QListWidget(self)

        self.delivered_button = QPushButton("Vehicle Was Delivered", self)
        self.delivered_button.clicked.connect(self.mark_vehicle_delivered)

        self.not_delivered_button = QPushButton("Vehicle Wasn't Delivered", self)
        self.not_delivered_button.clicked.connect(self.show_not_delivered_info)

        self.exit_to_login_button = QPushButton('Exit to Login', self)  # Yeni eklenen buton
        self.exit_to_login_button.clicked.connect(self.exit_to_login)  # Yeni eklenen butonun baÄŸlantÄ±sÄ±

        layout = QVBoxLayout()
        layout.addWidget(self.current_datetime_label)
        layout.addWidget(self.vehicle_list_label)
        layout.addWidget(self.vehicle_list)
        layout.addWidget(self.delivered_button)
        layout.addWidget(self.not_delivered_button)
        layout.addWidget(self.exit_to_login_button)  # Yeni eklenen buton

        self.update_datetime_timer = QTimer(self)
        self.update_datetime_timer.timeout.connect(self.update_datetime)
        self.update_datetime_timer.start(1000)

        self.load_all_vehicles()

        self.setLayout(layout)
        self.show()

    def load_all_vehicles(self):
        self.vehicle_list.clear()
        all_vehicles = self.vehicles_collection.find()

        for vehicle in all_vehicles:
            if self.is_rental_expired(vehicle):
                testlim_status = " (Kiralama sÃ¼resi dolmuÅŸ)"
            else:
                testlim_status = " (Kiralama sÃ¼resi dolmamÄ±ÅŸ)"
            rental_end_time = vehicle.get('rental_end_time', None)
            rental_end_time_str = rental_end_time.strftime("%Y-%m-%d %H:%M:%S") \
                if rental_end_time \
                else "BelirtilmemiÅŸ"
            item_text = f"{vehicle['brand']} {vehicle['model']} ({vehicle['year']}){testlim_status} - BitiÅŸ Tarihi: {rental_end_time_str}"
            self.vehicle_list.addItem(item_text)

    def update_datetime(self):
        self.current_datetime_label.setText('GÃ¼ncel Tarih ve Saat: ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    @staticmethod
    def is_rental_expired(vehicle):
        rental_end_time = vehicle.get('rental_end_time')

        if rental_end_time and rental_end_time < datetime.now():
            return True
        else:
            return False

    def mark_vehicle_delivered(self):
        selected_item = self.vehicle_list.currentItem()

        if selected_item:
            selected_vehicle_text = selected_item.text()
            selected_vehicle_parts = selected_vehicle_text.split(' ')
            brand = selected_vehicle_parts[0]
            model = selected_vehicle_parts[1]
            year = selected_vehicle_parts[2][1:-1]

            vehicle = self.vehicles_collection.find_one({'brand': brand, 'model': model, 'year': int(year)})

            if self.is_rental_expired(vehicle):
                self.vehicles_collection.update_one(
                    {'brand': brand, 'model': model, 'year': int(year)},
                    {'$set': {'available': True, 'kiralayan_kisi': None, 'rental_end_time': None}}
                )

                QMessageBox.information(self, 'Success', 'AraÃ§ teslim edildi ve durumu gÃ¼ncellendi.')
                self.load_all_vehicles()
            else:
                QMessageBox.warning(self, 'Error',
                                    'Bu aracÄ±n kiralama sÃ¼resi henÃ¼z dolmadÄ±ÄŸÄ±ndan teslim iÅŸlemi yapÄ±lamaz.')
        else:
            QMessageBox.warning(self, 'Error', 'LÃ¼tfen bir araÃ§ seÃ§in.')

    def show_not_delivered_info(self):
        selected_item = self.vehicle_list.currentItem()

        if selected_item:
            selected_vehicle_text = selected_item.text()
            selected_vehicle_parts = selected_vehicle_text.split(' ')
            brand = selected_vehicle_parts[0]
            model = selected_vehicle_parts[1]
            year = selected_vehicle_parts[2][1:-1]

            vehicle = self.vehicles_collection.find_one({'brand': brand, 'model': model, 'year': int(year)})

            if 'kiralayan_kisi' in vehicle:
                renting_user_id = vehicle['kiralayan_kisi']
                if renting_user_id is not None:
                    renting_user = self.main_window.users_collection.find_one({'_id': renting_user_id})
                    if renting_user:
                        QMessageBox.information(self, 'Not Delivered Info', f"{selected_vehicle_text}: "
                                                                            f"Kiralayan KullanÄ±cÄ±: {renting_user['username']}")
                    else:
                        QMessageBox.warning(self, 'Error', 'Kiralayan kullanÄ±cÄ± bilgileri bulunamadÄ±.')
                else:
                    QMessageBox.warning(self, 'Error', 'Bu araÃ§ henÃ¼z teslim edilmemiÅŸ.')
            else:
                QMessageBox.warning(self, 'Error', 'Bu araÃ§ henÃ¼z teslim edilmemiÅŸ.')
        else:
            QMessageBox.warning(self, 'Error', 'LÃ¼tfen bir araÃ§ seÃ§in.')

    def exit_to_login(self):
        self.main_window.show()
        self.close()


if __name__ == '__main__':
    app = QApplication([])
    car_rental_app = CarRentalApp()
    sys.exit(app.exec())
