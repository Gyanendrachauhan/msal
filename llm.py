from dotenv import load_dotenv
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
import PyPDF2,io


conversation = None



data_d = {}
chat_history_payload = {}



def get_pdf_texts_from_content(pdf_contents):
    text = ""
    for content in pdf_contents:
        with io.BytesIO(content) as stream:
            reader = PyPDF2.PdfReader(stream)
            for page in reader.pages:
                text += page.extract_text()
    # print(text)
    return text



def get_text_chunks(raw_text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(raw_text)
    return chunks


def get_vectorstore(text_chunks):
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore


def get_conversation_chain(vectorstore):
    # Context size if 3800 by default
    # llm = ChatOpenAI()
    llm = ChatOpenAI(model_name='gpt-3.5-turbo-16k')
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return conversation_chain


def handle_userinput(user_question):
    global conversation
    response = conversation({'question': user_question})

    # store updated conversation object to the dictionary data_d
    chat_history = response['chat_history']
    return chat_history


def upload(pdf_contents):
    # Check env load
    print("Env files Loaded")
    load_dotenv()

    # get pdf text
    raw_text = get_pdf_texts_from_content(pdf_contents)

    # Check if the uploaded document could not be parsed
    if len(raw_text) == 0:
        return {"error": "Unreadable document", "status_code": 400}

    # get the text chunks
    text_chunks = get_text_chunks(raw_text)

    # create vector store
    vectorstore = get_vectorstore(text_chunks)

    # Create conversation chain
    global conversation
    conversation = get_conversation_chain(vectorstore)

    # Here, you can add any additional processing or uploading steps if needed.

    return 200




def message(question_payload):


        # Store question in  history
    # try:
    #     chat_history_payload[email]['messages'].append(question_payload)
    # except:
    #     chat_history_payload[email].update({'messages': []})
    #     chat_history_payload[email]['messages'].append(question_payload)

        load_dotenv()

        # Get the question string from the input string
        question = question_payload
        # input question
        print(question)


        chat_history = handle_userinput(question)
        # print(chat_history)

        message_lis = [message.content for message in chat_history]


        response  = message_lis[-1]
        return response
