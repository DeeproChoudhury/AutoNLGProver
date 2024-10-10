Install PiSA and Isabelle 2022 following the instructions at https://github.com/albertqjiang/Portal-to-ISAbelle.

After this, put the corresponding download locations for Isabelle 2022 and PiSA in `Prover.py`.
This repository requires an Isabelle server to be started for verification. Provisionally this should be on port 8000. You can do this by running `start_server.py` replacing the path to
PiSA with your own.

### Run evaluations
This repository currently supports inference with both OpenAI and Mistral models.

- Please save your Mistral API key in the environment variable `MISTRAL_API_KEY`. For OpenAI, you can
    use the `OPENAI_API_KEY` environment variable, or the `OPENAI_ORGANISATION` variable for the organisation id.
- To run the system on the MiniF2F dataset, run the file `runs/run_full.sh`. This will run the system on both the test set and validation set. The results will be saved to a json file named ` proof_results.json`.
- The shell scripts allow for modification of the choice of models, input/output/prompt directories, the temperature, timeout and type of models used. Note that as mistral and OpenAI models have different APIs, you must specify the model type in the shell script.
- The mistral models supported are `mistral-large`, `nemo` and `codestral`.
