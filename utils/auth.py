import os
import base64
import argon2
from argon2 import PasswordHasher

class Auth:
    def __init__(self, db):
        self.db = db
        self.ph = PasswordHasher(
            time_cost=3,      # Número de iteraciones
            memory_cost=65536,  # Uso de memoria en kb (64 MB)
            parallelism=4,    # Grado de paralelismo
            hash_len=32,      # Longitud del hash
            salt_len=16       # Longitud de la sal
        )
    
    def register_user(self, username, password, user_level=1):
        """Registrar un nuevo usuario en el sistema."""
        # Verificar si el usuario ya existe
        existing_user = self.db.get_user(username)
        if existing_user:
            return False, "Username already taken"
        
        # Generar salt
        salt = os.urandom(16)
        salt_b64 = base64.b64encode(salt).decode('utf-8')
        
        # Contraseña Hash con salt
        try:
            password_hash = self.ph.hash(password + salt_b64)
            user_id = self.db.add_user(username, password_hash, salt_b64, user_level)
            if user_id:
                return True, user_id
            return False, "Failed to add user to database"
        except Exception as e:
            return False, str(e)
    
    def login(self, username, password):
        """Authenticate a user and return user details if successful."""
        user = self.db.get_user(username)
        if not user:
            return False, "Invalid username or password"
        
        user_id, username, password_hash, salt_b64, user_level = user
        
        try:
            # Verificar la contraseña
            self.ph.verify(password_hash, password + salt_b64)
            # Verificar si el hash necesita rehashing
            if self.ph.check_needs_rehash(password_hash):
                new_hash = self.ph.hash(password + salt_b64)
                self.db.update_user_password(user_id, new_hash)
            
            return True, {"id": user_id, "username": username, "level": user_level}
        except argon2.exceptions.VerifyMismatchError:
            return False, "Invalid username or password"
        except Exception as e:
            return False, str(e) 