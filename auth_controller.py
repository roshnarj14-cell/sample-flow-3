"""Auth Controller"""
from database import get_connection, hash_password


class AuthController:
    @staticmethod
    def login(username: str, password: str):
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=? AND active=1",
            (username, hash_password(password))
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_all_users():
        conn = get_connection()
        rows = conn.execute("SELECT * FROM users ORDER BY full_name").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def create_user(username, password, full_name, role, email=""):
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO users(username,password,full_name,role,email) VALUES(?,?,?,?,?)",
                (username, hash_password(password), full_name, role, email)
            )
            conn.commit()
            return True, "User created successfully"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def update_user(user_id, full_name, role, email, active):
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE users SET full_name=?,role=?,email=?,active=? WHERE id=?",
                (full_name, role, email, active, user_id)
            )
            conn.commit()
            return True, "Updated"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def change_password(user_id, new_password):
        conn = get_connection()
        conn.execute("UPDATE users SET password=? WHERE id=?",
                     (hash_password(new_password), user_id))
        conn.commit()
        conn.close()
