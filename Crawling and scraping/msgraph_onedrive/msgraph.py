import webbrowser
import msal
import os
from shared.globals import TOKEN_CACHE_PATH

MS_GRAPH_BASE_URL = 'https://graph.microsoft.com/v1.0'

def get_access_token(application_id, client_secret, scopes):
    token_cache = msal.SerializableTokenCache()  # Tạo token cache

    # Nếu file cache tồn tại, đọc dữ liệu vào token cache
    if os.path.exists(TOKEN_CACHE_PATH):
        with open(TOKEN_CACHE_PATH, "r") as f:
            token_cache.deserialize(f.read())
    
    client = msal.ConfidentialClientApplication(
        client_id=application_id,
        client_credential=client_secret,
        authority='https://login.microsoftonline.com/consumers/',
        token_cache=token_cache  # Sử dụng cache
    )

    accounts = client.get_accounts()
    print("Accounts:", accounts)

    # Nếu có tài khoản trong cache, thử lấy token qua `acquire_token_silent`
    if accounts:
        chosen_account = accounts[0]  # Chọn tài khoản đầu tiên
        print(f"Using account: {chosen_account['username']}")
        token_response = client.acquire_token_silent(scopes, account=chosen_account)
        if token_response and 'access_token' in token_response:
            print("Access token acquired silently.")
            return token_response['access_token']

    # Nếu không có token hoặc tài khoản, thực hiện luồng xác thực bằng trình duyệt
    auth_request_url = client.get_authorization_request_url(scopes)
    print(auth_request_url)

    webbrowser.open(auth_request_url)

    authorization_code = input('Enter the authorization code: ')

    token_response = client.acquire_token_by_authorization_code(
        code=authorization_code,
        scopes=scopes
    )
    
    # Lưu cache lại sau khi nhận được token
    with open(TOKEN_CACHE_PATH, "w") as f:
        f.write(token_cache.serialize())

    if 'access_token' in token_response:
        return token_response['access_token']
    else:
        raise Exception('Failed to acquire access token: ' + str(token_response))