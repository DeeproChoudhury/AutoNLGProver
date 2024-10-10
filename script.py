from langchain_utils import LLMMixture
from LemmaSketcher import LemmaSketcher
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from Orienter import Orienter
from test import thoughts_queue_3
from typing import List, Dict
import os
import json
from absl import app, flags, logging
from concurrent.futures import ThreadPoolExecutor, as_completed

FLAGS = flags.FLAGS
flags.DEFINE_string("model", "mistral-large", "The model to use for the language model")
flags.DEFINE_string("input_directory", "data/full_data/test", "The directory containing the input JSON files")
flags.DEFINE_string("messages_directory", "data/full_data/test_messages", "The directory to save the messages as JSON files")
flags.DEFINE_string("output_directory", "data/full_data/test_output", "The directory to save the responses as JSON files")
flags.DEFINE_float("temperature", 0.0, "The temperature to use for the language model")
flags.DEFINE_integer("request_timeout", 120, "The request timeout to use for the language model")
flags.DEFINE_string("type", "mistral", "The type of language model to use")
flags.DEFINE_integer("num_runs", 100, "The number of runs to use for the language model")
flags.DEFINE_list("directories", ["/data/test_data/"], "The directories containing the datasets")

def extract_components_from_json(filepath):
    with open(filepath, "r") as file:
        data = json.load(file)
    
    problem_name = data.get("problem_name", "")
    category = data.get("category", "")
    metadata = data.get("metadata", {})
    informal_statement = data.get("informal_statement", "")
    informal_proof = data.get("informal_proof", "")
    formal_statement = data.get("formal_statement", "")
    formal_code = data.get("formal_code", "")
    
    return {
        "problem_name": problem_name,
        "category": category,
        "metadata": metadata,
        "informal_statement": informal_statement,
        "informal_proof": informal_proof,
        "formal_statement": formal_statement,
        "formal_code": formal_code
    }

def message_to_dict(message):
    return {
        "role": message.type,
        "content": message.content
    }

def save_messages_to_json(messages: List[Dict[str, str]], directory: str, run_number: int):
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, f"run_{run_number}.json")
    messages_as_dicts = [message_to_dict(msg) for msg in messages]
    with open(filepath, "w") as file:
        json.dump(messages_as_dicts, file, indent=4)

def load_process_and_save_all(input_directory, messages_directory, orienter, runs=100):
    for file in sorted(os.listdir(input_directory)):
        if file.endswith(".json"):
            filepath = os.path.join(input_directory, file)
            components = extract_components_from_json(filepath)
            
            problem_name = os.path.splitext(file)[0]
            problem_directory = os.path.join(messages_directory, problem_name)
            
            for i in range(1, runs + 1):
                messages = orienter.render_messages(
                    informal_statement=components["informal_statement"],
                    informal_proof=components["informal_proof"],
                    formal_statement=components["formal_statement"]
                )
                save_messages_to_json(messages, problem_directory, i)
            print(f"Saved {runs} runs of oriented messages for {file} in {problem_directory}")

def dict_to_message(message_dict):
    print("Message: ", message_dict)
    if message_dict["role"] == "system":
        return SystemMessage(message_dict["content"])
    elif message_dict["role"] == "human":
        return HumanMessage(message_dict["content"])
    elif message_dict["role"] == "ai":
        return AIMessage(message_dict["content"])
    else:
        raise ValueError("Invalid message role")
        
def load_message_pair(filename: str):
    print(filename)
    with open(filename, "r") as f:
        messages_as_dicts = json.load(f)
    # messages_as_dicts = json.loads(messages_as_dicts)
    print("Messages as dicts: ", messages_as_dicts)
    # return dict_to_message(messages_as_dicts)
    return [dict_to_message(msg) for msg in messages_as_dicts]  

def save_responses_to_json(responses: List[str], directory: str, run_number: int):
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, f"run_{run_number}.txt")
    with open(filepath, "w") as file:
        file.write(responses)
        # json.dump(responses, file, indent=4)

def query_extracted_messages(messages_directory: str, responses_directory: str, model_name: str, temperature: float = 0.0, request_timeout: int = 120, logger=None, type="openai"):
    print("Querying extracted messages")
    llm = LLMMixture(
        model_name=model_name,
        temperature=temperature,
        request_timeout=request_timeout,
        logger=logger,
        type=type
    )

    for file in os.listdir(messages_directory):
        if file.endswith(".json"):
            filepath = os.path.join(messages_directory, file)
            print("Filepath: ", filepath)
            messages = load_message_pair(filepath)
            print("Messages: ", messages)
            response = llm.query(langchain_msgs=messages, temperature=temperature, max_tokens=4000)
            save_responses_to_json(response, responses_directory, int(file.split('_')[1].split('.')[0]))

            
def thoughts_queue_dataset(n=100, directories = None):

    if directories is None:
        directories = FLAGS.directories

    results = []

    all_problems = set()
    verified_problems = set()

    logging.set_verbosity(logging.INFO)
    logger = logging

    for dir_path in directories:
        for filename in os.listdir(dir_path):
            if filename.endswith('.json'):
                filepath = os.path.join(dir_path, filename)
                with open(filepath, 'r') as f:
                    problem_data = json.load(f)
                    informal_statement = problem_data.get('informal_statement', '')
                    informal_proof = problem_data.get('informal_proof', '')
                    formal_statement = problem_data.get('formal_statement', '')
                    problem_name = problem_data.get('problem_name', filename)
                    
                    all_problems.add(problem_name)
                    
                    problem_results = []

                    problem_solved = False

                    for run_index in range(n):
                        try:
                            print(f"Processing {problem_name}, Run {run_index+1}/{n}")
                            logger.info(f"Processing {problem_name}, Run {run_index+1}/{n}")

                            final_sketch, verified_lemmas, success = thoughts_queue_3(
                                informal_statement,
                                informal_proof,
                                formal_statement,
                                type="mistral",
                                use_codestral=True
                            )

                            result = {
                                'problem_name': problem_name,
                                'run_index': run_index,
                                'success': success,
                                'final_sketch': final_sketch,
                                'verified_lemmas': verified_lemmas
                            }
                            problem_results.append(result)

                            if success:
                                problem_solved = True
                                print(f"Problem {problem_name} solved on run {run_index+1}")
                                logger.info(f"Problem {problem_name} solved on run {run_index+1}")
                            else:
                                logger.info(f"Problem {problem_name} failed on run {run_index+1}")
                        except Exception as e:
                            error_message = f"Error processing {problem_name}, run {run_index+1}: {e}"
                            print(error_message)
                            logger.error(error_message)
                            problem_results.append({
                                'problem_name': problem_name,
                                'run_index': run_index,
                                'success': False,
                                'error': str(e)
                            })
                    results.extend(problem_results)

                    if problem_solved:
                        verified_problems.add(problem_name)
                        success_message = f"Problem {problem_name} verified successfully in at least one attempt."
                        print(success_message)
                        logger.info(success_message)
                    else:
                        failure_message = f"Problem {problem_name} was not verified in any of the {n} attempts."
                        print(failure_message)
                        logger.info(failure_message)

    unsolved_problems = all_problems - verified_problems

    with open('proof_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    with open('solved_problems.json', 'w') as f:
        json.dump(sorted(list(verified_problems)), f, indent=2)
    with open('unsolved_problems.json', 'w') as f:
        json.dump(sorted(list(unsolved_problems)), f, indent=2)

    total_verified = len(verified_problems)
    total_unsolved = len(unsolved_problems)
    total_problems = len(all_problems)
    summary_message = f"Total problems verified successfully: {total_verified} out of {total_problems}"
    print(summary_message)
    logger.info(summary_message)
    summary_message_unsolved = f"Total problems not verified: {total_unsolved} out of {total_problems}"
    print(summary_message_unsolved)
    logger.info(summary_message_unsolved)

    return results, verified_problems, unsolved_problems

def run_thoughts_queue_3_on_dataset(n=100):

    directories = ['/data/full_data/test/', '/data/full_data/valid/']

    results = []

    def process_run(run_index, problem_name, informal_statement, informal_proof, formal_statement):
        try:
            print(f"Processing {problem_name}, Run {run_index+1}/{n}")
            final_sketch, verified_lemmas, success = thoughts_queue_3(
                informal_statement,
                informal_proof,
                formal_statement
            )
            result = {
                'problem_name': problem_name,
                'run_index': run_index,
                'success': success,
                'final_sketch': final_sketch,
                'verified_lemmas': verified_lemmas
            }
            return result
        except Exception as e:
            print(f"Error processing {problem_name}, run {run_index+1}: {e}")
            return {
                'problem_name': problem_name,
                'run_index': run_index,
                'success': False,
                'error': str(e)
            }

    for dir_path in directories:
        for filename in os.listdir(dir_path):
            if filename.endswith('.json'):
                filepath = os.path.join(dir_path, filename)
                with open(filepath, 'r') as f:
                    problem_data = json.load(f)
                    informal_statement = problem_data.get('informal_statement', '')
                    informal_proof = problem_data.get('informal_proof', '')
                    formal_statement = problem_data.get('formal_statement', '')
                    problem_name = problem_data.get('problem_name', filename)
                    
                    problem_results = []

                    with ThreadPoolExecutor() as executor:
                        futures = [
                            executor.submit(
                                process_run,
                                run_index,
                                problem_name,
                                informal_statement,
                                informal_proof,
                                formal_statement
                            ) for run_index in range(n)
                        ]

                        for future in as_completed(futures):
                            result = future.result()
                            problem_results.append(result)

                    results.extend(problem_results)

    with open('thoughts_queue_3_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    return results

def main(_):
    n = FLAGS.num_runs
    results, verified_problems, unsolved_problems = thoughts_queue_dataset(n=n, directories=FLAGS.directories)
    # thoughts_queue_dataset(n=2, directories = ['data/test_data/'])
    # input_directory = FLAGS.input_directory
    # messages_directory = FLAGS.messages_directory
    # output_directory = FLAGS.output_directory
    # runs = FLAGS.num_runs
    # orienter = Orienter(
    #     model=FLAGS.model
    # )

    # load_process_and_save_all(input_directory, messages_directory, orienter, runs=runs)
    # for directory in os.listdir(messages_directory):
    #    print("Directory: ", directory)
    #     query_extracted_messages(f"{messages_directory}/{directory}", output_directory, FLAGS.model, FLAGS.temperature, FLAGS.request_timeout, logger=None, type=FLAGS.type)
         
if __name__ == "__main__":
    app.run(main)
    # input_directory = "data/full_data/test"
    # input_directory = "test_input"
    # output_directory = "test_output"
    # orienter = Orienter(
    #     model="mistral-large"
    # )

    # query_extracted_messages(input_directory, output_directory, "mistral-large", temperature=0.0, request_timeout=120, logger=None, type="mistral")

    # load_process_and_save_all(input_directory, output_directory, orienter, runs=100)