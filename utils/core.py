import secrets, string

# This file contains utility functions for the application.
# The functions are used to generate random strings for user IDs and passwords.
def generate_user_id():

    alphabet = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(16))