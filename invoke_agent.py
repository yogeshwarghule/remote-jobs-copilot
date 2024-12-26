import io
import boto3
from botocore.exceptions import ClientError

agentId = "RT4T06C1KO" 
agentAliasId = "KQT2WRPAUR"
AWS_REGION = "us-east-1"


def invoke_agent_data(prompt, session_id, end_session):
    try:
        client = boto3.session.Session(region_name=AWS_REGION).client(service_name="bedrock-agent-runtime", region_name=AWS_REGION)
        
        response = client.invoke_agent(
            agentId=agentId,
            agentAliasId=agentAliasId,
            enableTrace=True,
            sessionId=session_id,
            inputText=prompt,
            endSession=end_session
        )

        output_text = ""
        citations = []
        trace = {}
        
        has_guardrail_trace = False

        for event in response.get("completion"):
            # Combine the chunks to get the output text
            if "chunk" in event:
                chunk = event["chunk"]
                output_text += chunk["bytes"].decode()
                if "attribution" in chunk:
                    citations = citations + chunk["attribution"]["citations"]

            # Extract trace information from all events
            if "trace" in event:
                for trace_type in ["guardrailTrace", "preProcessingTrace", "orchestrationTrace", "postProcessingTrace"]:
                    if trace_type in event["trace"]["trace"]:
                        mapped_trace_type = trace_type
                        if trace_type == "guardrailTrace":
                            if not has_guardrail_trace:
                                has_guardrail_trace = True
                                mapped_trace_type = "preGuardrailTrace"
                            else:
                                mapped_trace_type = "postGuardrailTrace"
                        if trace_type not in trace:
                            trace[mapped_trace_type] = []
                        trace[mapped_trace_type].append(event["trace"]["trace"][trace_type])

    except ClientError as e:
        raise e

    return output_text, trace


def askQuestion(question, sessionId, endSession=False):
    try:
        return invoke_agent_data(question, sessionId, endSession)
    except Exception as e:
        raise e


def lambda_handler(event, context):
    
    sessionId = event["sessionId"]
    question = event["question"]
    endSession = False
    
    print(f"Session: {sessionId} asked question: {question}")
    
    try:
        if (event["endSession"] == "true"):
            endSession = True
    except:
        endSession = False
    
    try: 
        response, trace_data = askQuestion(question, sessionId, endSession)
        
        return response, trace_data
    except Exception as e:
        raise e

