import uuid
import requests
from flask import Flask, render_template, session, request, redirect, url_for,jsonify,json
from flask_session import Session
import msal
import app_config
from dotenv import load_dotenv
import os
from llm import message
from share import get_access_token,download_pdf_files,upload_pdfs_to_server,fetch_pdf_content

cwd = os.getcwd()
load_dotenv()

folder_files_dict = {}
file_link_dict = {}

app = Flask(__name__)
app.config.from_object(app_config)
Session(app)


client_id = os.getenv('client_id')
client_secret = os.getenv('client_secret')
tenant_id = os.getenv('tenant_id')
resource = os.getenv('resource')
site_id = os.getenv('site_id')
base_url = f'https://graph.microsoft.com/v1.0/sites/{site_id}/drive/items'
auth_li={}



# This section is needed for url_for("foo", _external=True) to automatically
# generate http scheme when this sample is running on localhost,
# and to generate https scheme when it is deployed behind reversed proxy.
# See also https://flask.palletsprojects.com/en/1.0.x/deploying/wsgi-standalone/#proxy-setups
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

cid_dic = []


@app.route("/")
def index():
    if not session.get("user"):
        return redirect(url_for("login"))
    return render_template('index.html', user=session["user"], version=msal.__version__)

@app.route("/webhook", methods=['POST'])
def webhook():
    access_token = get_access_token()
    if not access_token:
        print("Failed to retrieve access token.")
        exit()
    base_url = f'https://graph.microsoft.com/v1.0/sites/{site_id}/drive/items'
    folder_id = "root"
    folder_name = ""
    # result, all_files,file_url_dict  = download_pdf_files(folder_id, folder_name, access_token,base_url)
    # clean_local_directory(all_files)
    # print(all_files)
    # print(file_url_dict)
    # print(result)

    payload = request.form
    data = payload['intent']
    data1 = json.loads(data)
    # print(data1)
    action = data1['fulfillment']['action']
    parameters = data1['fulfillment']['parameters']
    if action == "action-vecv-user-pre-login":
            chatId = data1["chatId"]
            auth_li[chatId] = {}
            res_json = {"id":3,"message":"Get verified from AD","fulfillment":{"action":"action-vecv-user-pre-login","parameters":{"details":"{previousValue:2}"},"previousIntent":2},"metadata":{"payload":[{"url":f"https://b832-106-221-229-17.ngrok-free.app/login?cid={chatId}","name":". Go to AD Login page","image":"https://i.ibb.co/KNFsKWX/images.png","type":"link","value":"Go to AD Login page","trigger":210,"openLinkInNewTab":True}],"templateId":6},"userInput":False}

            return res_json
    elif action == "action-user-vecv-login":
            chatId = str(data1["chatId"])
            print(chatId)
            with open(r"C:\Users\Gyani\Desktop\ms-identity-python-webapp-master\auth.txt","r") as f:
                txt=f.read()
            if len(txt)!=0:
                l =  txt.split(":")
                c_i = str(l[0])
                auth = str(l[1])
                print(c_i)
                print(auth)
                if chatId == c_i:
                    if auth == "true":
                        return data1


            res_json = {"id": 210, "message": "Not verified! <b>Try Again", "metadata": {
                    "payload": [{"label": "Validate", "value": "Validate ", "trigger": 2100},
                                {"image": "https://img.icons8.com/flat-round/2x/circled-left.png", "label": "Go Back",
                                 "value": "Go Back", "trigger": 3}], "templateId": 6}, "userInput": False}
            return res_json

    if action =="action-category-question":
        question = parameters['question']
        print(question)
        x = message(question)
        print(x)
        c = {"message": x, "id": 40, "userInput": True, "trigger": 400}
        return jsonify(c)

    elif action == "action-category-faq-ma":
    # Present the list of folder names from SharePoint
        global file_link_dict,folder_files_dict
        folder_files_dict,_,file_link_dict = download_pdf_files(folder_id, folder_name, access_token, base_url)

        if not folder_files_dict:
            folder_files_dict = {}

    # Extract folder names for the checkbox list

        folder_names = list(folder_files_dict.keys())
        selected_list = [{"value": folder, "label": folder} for folder in folder_names]
    # print(selected_list)

        return jsonify({
        "id": 302,
        "message": "Welcome to our Sharepoint Site and select folders for Q&A",
        "metadata": {
            "message": "something went wrong. Submit details again",
            "payload": [
                {
                    "data": {
                        "name": "Checkbox",
                        "title": "Checkbox",
                        "options": selected_list
                    },
                    "name": "Checkbox",
                    "type": "checkbox",
                    "validation": "required"
                },
                {
                    "type": "submit",
                    "label": "Submit",
                    "message": "Response Submitted",
                    "trigger": 30200,
                    "formAction": "/",
                    "requestType": "POST"
                },
                {
                    "type": "cancel",
                    "label": "Cancel",
                    "message": "Cancelled",
                    "trigger": 30
                }
            ],
            "templateId": 13,
            "contentType": "300"
        },
        "userInput": False,
        "fulfillment": {
            "action": "action-category-faq-ma",
            "parameters": {
                "faq": "{previousValue:30}"
            },
            "previousIntent": 30
        }
    })
    if action == "action-filename":
    # Get the list of selected folders
        selected_folder_names = parameters['faq']['Checkbox']

    # This will store filenames from all selected folders
        all_filenames = []

    # Loop through each selected folder and gather filenames
        for selected_folder_name in selected_folder_names:
            print(selected_folder_name)

        # Fetch filenames for the current selected folder
            filenames_in_selected_folder = folder_files_dict.get(selected_folder_name, [])

        # Add the filenames of the current folder to the all_filenames list
            all_filenames.extend(filenames_in_selected_folder)

    # Convert the list of filenames to the desired options format
        options_list = [{"value": filename, "label": filename} for filename in all_filenames]

        return jsonify({
        "id": 30200,
        "message": "This is Multiple-Auto Suggestion Intent",
        "trigger": 3020,
        "userInput": True,
        "inputOptions": {
            "type": "auto-suggest",
            "options": options_list,
            "multiple": True,
            "optional": False
        },"fulfillment": {
        "action": "action-filename",
        "parameters": {
            "faq": "{previousValue:302}"
        },
        "previousIntent": 302
    }
    })


    if action == "action-category-faq-ma-ans":
        folder_files_dict, file_identifiers, file_link_dict = download_pdf_files(folder_id, folder_name, access_token, base_url)
        print(file_link_dict)


        # file_url_dict  = download_pdf_files(folder_id, folder_name, access_token,base_url)
        selected_web_urls = [file_link_dict[filename['label']] for filename in parameters['faqans'] if filename['label'] in file_link_dict]
        # print(selected_web_urls)
        response = upload_pdfs_to_server(selected_web_urls, access_token, base_url)
        # response_selected_filenames = "".join("<li>"+i+"</li>" for i in parameters['faqans']['Checkbox'])
        response_selected_filenames = "".join("<li>"+i['label']+"</li>" for i in parameters['faqans'] if i['label'] in file_link_dict)
        print("DEBUG: response_selected_filenames contents:", response_selected_filenames)

        if response:
            return jsonify({
                "id": 3020,
                "message": "<ul>" + response_selected_filenames + "</ul> Uploaded and trained successfully",
                "metadata": {
                    "payload": [{
                        "image": "https://img.icons8.com/flat-round/2x/circled-left.png",
                        "label": "Ask Question",
                        "value": "Ask Question",
                        "trigger": 4
                    }],
                    "templateId": 6
                },
                "fulfillment": {
                    "action": "action-category-faq-ma-ans",
                    "parameters": {},
                    "previousIntent": 30200
                },
                "userInput": False
            })
        else:
            return jsonify({
                "error": f"Failed to upload and train with {response_selected_filenames}",
                "response_text": response.text if hasattr(response, 'text') else str(response),
                "response_status": response.status_code if hasattr(response, 'status_code') else None,
                "id": 304,  # You can set the appropriate ID
                "userInput": True,
                "trigger": 304  # You can set the appropriate trigger # You can set the appropriate trigger
                    })


@app.route("/login")
def login():
    # Technically we could use empty list [] as scopes to do just sign in,
    # here we choose to also collect end user consent upfront
    cid = request.args.get("cid")
    cid_dic.insert(0,cid)

    session["flow"] = _build_auth_code_flow(scopes=app_config.SCOPE)
    return render_template("login.html", auth_url=session["flow"]["auth_uri"], version=msal.__version__)

@app.route(app_config.REDIRECT_PATH)  # Its absolute URL must match your app's redirect_uri set in AAD
def authorized():
    try:
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_auth_code_flow(
            session.get("flow", {}), request.args)
        if "error" in result:
            with open(r"C:\Users\Gyani\Desktop\ms-identity-python-webapp-master\auth.txt","w") as f:
                f.write(f"{cid_dic[0]}:false")
            return render_template("auth_error.html", result=result)
        with open(r"C:\Users\Gyani\Desktop\ms-identity-python-webapp-master\auth.txt","w") as f:
            f.write(f"{cid_dic[0]}:true")
        session["user"] = result.get("id_token_claims")
        _save_cache(cache)
    except ValueError:  # Usually caused by CSRF
        pass  # Simply ignore them
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()  # Wipe out user and its token cache from session
    return redirect(  # Also logout from your tenant's web session
        app_config.AUTHORITY + "/oauth2/v2.0/logout" +
        "?post_logout_redirect_uri=" + url_for("index", _external=True))

@app.route("/graphcall")
def graphcall():
    token = _get_token_from_cache(app_config.SCOPE)
    if not token:
        return redirect(url_for("login"))
    graph_data = requests.get(  # Use token to call downstream service
        app_config.ENDPOINT,
        headers={'Authorization': 'Bearer ' + token['access_token']},
        ).json()
    return render_template('display.html', result=graph_data)


def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()

def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        app_config.CLIENT_ID, authority=authority or app_config.AUTHORITY,
        client_credential=app_config.CLIENT_SECRET, token_cache=cache)

def _build_auth_code_flow(authority=None, scopes=None):
    return _build_msal_app(authority=authority).initiate_auth_code_flow(
        scopes or [],
        redirect_uri=url_for("authorized", _external=True))

def _get_token_from_cache(scope=None):
    cache = _load_cache()  # This web app maintains one cache per session
    cca = _build_msal_app(cache=cache)
    accounts = cca.get_accounts()
    if accounts:  # So all account(s) belong to the current signed-in user
        result = cca.acquire_token_silent(scope, account=accounts[0])
        _save_cache(cache)
        return result

app.jinja_env.globals.update(_build_auth_code_flow=_build_auth_code_flow)  # Used in template

if __name__ == "__main__":
    app.run(debug=True)

