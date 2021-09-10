# Local endpoints for offline testing

LOCAL_CLEAN_URL = 'http://localhost:5000/clean'
LOCAL_RECEIVER_URL = 'http://localhost:5000/receiver'
LOCAL_REASSEMBLE_URL = 'http://localhost:5000/reassemble'
LOCAL_TEST_URL = 'http://localhost:5000/test'
LOCAL_CLEAN_WINDOW_URL = 'http://localhost:5000/clean_window'

# Local variables:
cwd = 'receiver'
PAYLOAD = f'{cwd}/testing/packets/300'
REASSEMBLED = f'{cwd}/testing/reassembled'
