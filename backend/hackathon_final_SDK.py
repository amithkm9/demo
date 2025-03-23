################################### MODELS AND REQUIREMENTS ##############################

## together = c481a3528fbff4fe8004828415960962599af57549a51ef039096e0f2bd434ed


##################################
from langchain_aws import ChatBedrock
import base64
from langchain_together import ChatTogether
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


# vector_store.add_documents(documents=docs)
# BEDROCK LLAMA 3.1
chat1 = ChatBedrock(credentials_profile_name="<profile-name>", model="meta.llama3-70b-instruct-v1:0", region="us-east-1", model_kwargs={"max_tokens" : 4096})

## Wmbedding model

embeddings = BedrockEmbeddings(credentials_profile_name="<profile-name>", region_name="us-east-1")

# TOGETHER LLAMA 3.2 VISION INSTRUCT
chat = ChatTogether(
    together_api_key="<api-key>",
    model="meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
    max_tokens = 1000,
    temperature=0,
)


# FUNCTION CALLING
class Order_API_Input(BaseModel):
    name: str = Field(description = "Name of the product")
    quantity:int = Field(description= "quantity of the items")


@tool("place_order", args_schema=Order_API_Input, return_direct=True)
def place_order(name, quantity):
    """Places an Order using the API

    Args:
        name (_type_): name of the item
        quantity (_type_): quantity of the item

    Returns:
        dict : if call was success
    """
    return "Order Placed Succefully Items as \n {} : {}".format(name, quantity)

tools = [place_order]


llm = ChatOpenAI(
    base_url="<url>",
    api_key="<api-key>",
    model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
)

#llm_with_tools = chat1.bind_tools(tools)
llm_with_tools = llm.bind_tools(tools)


### RAG CHAIN ####
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import BedrockEmbeddings

docs = list()
pdf_file = "Drugs_and_Uses.pdf"
loader = PyPDFLoader(pdf_file)
pages = loader.load_and_split()

docs = docs + pages


embeddings = BedrockEmbeddings(credentials_profile_name="llama-agent", region_name="us-east-1")

## Qdrant Vector Store
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

client = QdrantClient(path="./qdrant_store_test")

client.create_collection(
    collection_name="demo_collection",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)

vector_store = QdrantVectorStore(
    client=client,
    collection_name="demo_collection",
    embedding=embeddings,
)

vector_store.add_documents(documents=docs)

retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k": 10})

prompt = hub.pull("rlm/rag-prompt")

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | chat1
    | StrOutputParser()
)


##

############################### Functions ################################

def order_based_on_image(quantity:str, image_64:str):
    # Step 1: Gather information like name of the medicine, contents if any, manufacturer, base info
    messages = [
        {
            "role" : "system", "content": [
            {"type": "text", "text": "Provided the image extract information like name of the medicine, its contents, manufacturer, usage. DO NOT make up anything if not known say unable to read image \n Do not provide information about background etc. Just focus on the medicine wrapper or bottle present in the image"}
        ]
        },

        {"role": "user", "content": [
            {"type": "image_url", "image_url": {
                "url": f"data:image/png;base64,{image_64}"}
            }
        ]}
    ]
    image_analysis = chat.invoke(messages)
    print(image_analysis.content)
    print("================")
    # Step 2: Extract Name of the medicine from the generation.

    prompt_extract_name = [
        {
            "role" : "system", "content": [
            {"type": "text", "text": "You will be provided with a passage that contains some information about a medicine which is interpreted from an image. Your Job is to extract the name of the medicine from the passage.\n PASSAGE: {} \n Important is to respond only the name of the medicine and nothing else.".format(image_analysis.content)}
        ]
        }
    ]
    extracted_name = chat1.invoke(prompt_extract_name)
    print(extracted_name.content)
    print("================")

    # Step 3: Order using the order llm.

    quantity = quantity

    build_query = "Please order {} : {}".format(quantity, extracted_name.content)

    print(build_query)
    print("================")
    messages = [HumanMessage(build_query)]
    ai_msg = llm_with_tools.invoke(messages)
    messages.append(ai_msg)
    for tool_call in ai_msg.tool_calls:
        selected_tool = {"place_order" : place_order}[tool_call["name"].lower()]
        tool_output = selected_tool.invoke(tool_call["args"])
        messages.append(ToolMessage(tool_output, tool_call_id=tool_call["id"]))

    return messages

## Information Based on image of prescription

def info_based_on_image_prescription(image_base:str, language:str = "English"):
    ## IF NOT ENGLISH :
        ## Convert the language english
    ## ELSE:
    messages = [
        {
            "role" : "system", "content": [
            {"type": "text", "text": "You are an expert in analyzing doctor handwritten notes, You will be provided with an image of medical prescription, You need to extract the medicines, dosage, and the short usage of the medicine. Present to user in tabular format. \n Few things to remember about the doctor :\n - Dr. writes the dosage as morning-afternoon-evening below the medicine as 1-0-0 which means medicine is to be taken in the morning.\n - numbers to right of the name of medicine shows total quantity. \n Tab. means Tablet \n If not known about the medicine say unknown in the column. No need to extract Information about the patient focus on the medicine only."}
        ]
        },

        {"role": "user", "content": [
            {"type": "image_url", "image_url": {
                "url": f"data:image/png;base64,{image_base}"}
            }
        ]}
    ]
    image_analysis = chat.invoke(messages)
   
    ### Generating RAG results 

    rag_prompt = """
        Given the following context (table of medicines), provide detailed information for each medicine listed, including:

        1. **Uses**: Explain what the medicine is typically used for, including any specific conditions or symptoms it treats.
        2. **How It Works**: Describe the mechanism of action, how the medicine works in the body.
        3. **Precautions**: Highlight what should be avoided while taking the medicine, such as dietary restrictions, drug interactions, and other important safety information.

        **Table of Medicines:**
        {}

        **Instructions**: There might be multiple medicines provided in the table. Please give information for each medicine listed, following the format below.

        ---

        **Format for Output:**

        **Medicine Name**: (Replace with the actual medicine name)
        - **Uses**: (What the medicine is used for)
        - **How It Works**: (Explanation of its mechanism)
        - **Precautions**: (What should be avoided, such as foods, activities, and interactions)

        **Example Output**:

        **Medicine 1**:
        - **Uses**: Used for treating mild to moderate pain, inflammation, or fever.
        - **How It Works**: This medicine works by inhibiting the production of chemicals that cause inflammation and pain in the body.
        - **Precautions**: Avoid taking this medicine on an empty stomach; avoid combining it with alcohol or other NSAIDs.

        **Medicine 2**:
        - **Uses**: Typically prescribed to treat bacterial infections.
        - **How It Works**: The medicine works by stopping the growth of bacteria in the body.
        - **Precautions**: Avoid direct exposure to sunlight or UV lamps while taking this medication, as it can cause sensitivity to light. Also, avoid taking antacids or calcium-rich products within a few hours of consumption.
        """.format(image_analysis.content)

    rag_outcome = rag_chain.invoke(rag_prompt)
    print("------------- This is RAG OUTCOME\n")
    print(rag_outcome)
    final_result = image_analysis.content + "\n\n" + rag_outcome
    
    conversion_language_prompt = "Provided is a piece of information in tabular format, convert the information as it is in devnagri {} language. Do not make any changes in the information \n INFORMATION : {}".format(language, final_result)
    converted = chat1.invoke(input = conversion_language_prompt)

    
    return converted.content

## Pipeline to generate Information based on image

def info_based_on_image(image_base:str, language:str = "English"):
    ## IF NOT ENGLISH :
        ## Convert the language english
    ## ELSE:
    messages = [
        {
            "role" : "system", "content": [
            {"type": "text", "text": "You are an expert in analyzing pictures of medicine bottles and wrappers, You will be provided with an image of medicine wrapper or box or bottle, You need to extract the medicines name,content, and the short usage of the medicine. Present to user in tabular format. \n If not known about the medicine say unknown in the column. No need to extract Information about the patient focus on the medicine only."}
        ]
        },

        {"role": "user", "content": [
            {"type": "image_url", "image_url": {
                "url": f"data:image/png;base64,{image_base}"}
            }
        ]}
    ]
    image_analysis = chat.invoke(messages)
    final_res = chat1.invoke("Convert the provided information in devnagri {} language, do not change any information. \n INFORMATION : {}".format(language, image_analysis.content))
    return final_res.content

## Pipeline to order based on the query

def order_based_on_name(query:str, language:str = "English"):

    # language Identify
    language_identify_prompt = "{}, Identify the language provided, response only with the language and nothing else\n eg if its marathi respond with 'Marathi' if Kannada respond with 'kannada'.".format(query)
    language = chat1.invoke(language_identify_prompt)
    language = language.content

    print(language)

    # language convert to english
    converted_query = chat1.invoke("Convert the sentence : {} to English\n Respond only with the converted text and nothing else, strictly adhere to the meaning of the sentence and the rules mentioned.".format(query))

    print(converted_query)

    messages = [HumanMessage(converted_query.content)]
    ai_msg = llm_with_tools.invoke(messages)
    messages.append(ai_msg)
    for tool_call in ai_msg.tool_calls:
        selected_tool = {"place_order" : place_order}[tool_call["name"].lower()]
        tool_output = selected_tool.invoke(tool_call["args"])
        messages.append(ToolMessage(tool_output, tool_call_id=tool_call["id"]))

    return messages[-1]

## Order Using Prescription

def order_based_on_image_prescription(image_64:str):
    # Step 1: Gather information like name of the medicine, contents if any, manufacturer, base info
    messages = [
        {
            "role" : "system", "content": [
            {"type": "text", "text": "Provided will be image of an medical prescription, You have to extract the following JSON, \n JSON : ('name of medicine 1' : ['quantity in number of tablets or bottles', 'what is the medicine used for']) \n for eg : if there is Calpol Tablet 3 days twice a day then response must be ('Calpol' : [6, 'Used to treat fever']) \n You are bound to follow the follwing Instructions \n INSTRUCTIONS : Response with JSON only and nothing else.\n If not known about the medicine usage say unknown. \n DO NOT Generate any other information or Put anything that is not in the image \n Remember this doctor writes #number for number of tablets or bottles "}
        ]
        },

        {"role": "user", "content": [
            {"type": "image_url", "image_url": {
                "url": f"data:image/png;base64,{image_64}"}
            }
        ]}
    ]
    image_analysis = chat.invoke(messages)
    print(image_analysis.content)
    print("================")
    # Step 2: Extract Name of the medicine from the generation.

    prompt_extract_name = [
        {
            "role" : "system", "content": [
            {"type": "text", "text": "You will be provided with a passage that contains some information about a medicine which is interpreted from an image, there will most probably be a JSON with structure as ('name of medicine 1' : ['quantity in number of tablets or bottles', 'what is the medicine used for']). You will have to figure out the name and quantity of the medicine and order them from the Order tool you have.".format(image_analysis.content)}
        ]
        }
    ]
    order = llm_with_tools.invoke(prompt_extract_name)
    print(order.content)
    print("================")

    messages = [HumanMessage(order.content)]
    ai_msg = llm_with_tools.invoke(messages)
    messages.append(ai_msg)
    for tool_call in ai_msg.tool_calls:
        selected_tool = {"place_order" : place_order}[tool_call["name"].lower()]
        tool_output = selected_tool.invoke(tool_call["args"])
        messages.append(ToolMessage(tool_output, tool_call_id=tool_call["id"]))

    return messages

