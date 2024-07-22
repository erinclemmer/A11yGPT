# Automatic Accessability fixing with ChatGPT

### Overview 
This project attempts to use ChatGPT to fix a variety of websites with accessability related issues. Various prompting algorithms are used to empirically test which method performs the best. Each prompting algorithm builds off of the last one. Guidance adds context to No Context, Few Shot adds examples to the context, Chain of Thought adds time to think on top of the examples, and Tree of Thought determines the best output using all of the approaches combined.

### Setup
To run the tests, you need to provide an API key for OpenAI. To do this create a `config.json` file in the base project directory. 
Inside this file there should be a property called `openai_api_key` with your api key in it. This file will not be committed to the repository.
```json
{
    "openai_api_key": "sk-xxxx"
}
```

### Main Algorithm
The main idea is to repeatedly prompt ChatGPT with the same input to determine the full set of possible responses. We run the `run_test` function for each prompting algorithm.

#### lib.run_test Function
Parameters:  
`get_fix`: (Function) The prompting algorithm under test. Takes a ChatGPT api interface, the text of the html file to fix, and the specific WCGA error to look for (if applicable, otherwise it is ignored), returns a JSON object of the output according to the SCHEMA supplied in the prompt.  
`test_folder`: (String) The folder with the system prompt in it. Expects there to be a `sys_prompt.txt` file in the folder supplied.  
`api_key`: (String) api_key to use for testing.  
`embed` (GptEmbed) the class used to create embeddings.  
`sim_threshold` (float) the maximum cosine similarity any fix should have with any other fix.  
`no_ctx` (Boolean) optional parameter (default false) to not iterate over each WCGA error type, only used in "No Context" folder.  
  
**If no_ctx is True**: iterates through each file in the `html` folder and runs `get_fixes_for_error` on them once.  
**If no_ctx is False**: Iterates through each file in the `html` folder and runs `get_fixes_for_error` for each wcga error type.
All returned fixes are added to the `fixes` folder with a sub folder name the same as the `test_folder` parameter value.

#### lib.get_fixes_for_error function
Parameters:  
`get_fix` (function) same as param of same name to `lib.run_test`.  
`chat`: (GptChat) object that allows sending prompts to the OpenAI api.  
`embed`: (GptEmbedding) object that allows creating embeddings from strings.  
`html`: (String) the text of the html file.  
`wcga_error`: (WCGAError) error data for a specific WCGA error.  
`sim_threshold`: (float) the maximum cosine similarity any fix should have with any other fix.  
  
This is the most important part of the algorithm. Essentially it repeatedly calls `get_fix` until it can't find any more "unique" (within specified bounds with `sim_threshold`) fixes. It runs in a while loop keeping track of an int called `retries`; each iteration of the loop it runs `get_fix` and creates an embedding for that fix. It then looks at every other fix that it has created and determines if any of those fixes have a cosine similarity greater than the `sim_threshold` parameter. If it is less than the threshold, the fix is added to the list of fixes and the `retries` variable is reset to 0. If it is greater than the threshold the `retries` variable is incremented. If the function returns a fix that surpasses the threshold five times in a row then it is determined that the output is "saturated" and the list of fixes is returned.

#### compile.compile function
Is responsible for taking the fixes from `lib.get_fixes_for_error` and checking them against the `violations.json` file. It tries to find the closest created fix to the ground truth error in `violations.json`. It does this by iterating through each prompting algorithm and each html file. For each *combination* of these it iterates through each violation in `violations.json` and finds the closest fixed line to the line supplied in `violations.json`. Creates the `output` folder.

## Project Structure
**Note:** Each prompting algorithm folder is in the form `t_Num_Description` so that it can be imported in python. Because the folder name is essentially a variable the folder name cannot start with a number.

#### Base python files
`gpt.py` holds classes related to the OpenAI api for easier use.  
`lib.py` holds miscellaneous library functions. Does not contain specific prompting algorithms.  
`unzip.py` script to unzip a set of zip files in a folder, find an html file in the unzipped contents, and adds the html files to a new folder. Not called in `main.py`.  
`main.py` running this script will replicate the experiment entirely. Takes multiple hours to run so be careful.  

#### Base json files
`config.json` non committed file for holding the OpenAI api key.  
`violations.json` an object that contains all of the violations for each html file. Each property of the main object must correlate to an html file name in the `html` folder. The array for the property consists of a guideline number for the violation and the line number of the violation. The guideline string must correlate to a definition in `wcga_errors.json`.  
`wcga_errors.json` an array of guidelines that will be used to determine violations. Each definition should contain the "guideline" property with serves as an id, the "success_criteria" property which is a short description of what the guideline means and an "examples" array that contains examples of the error and how it would be fixed.  

### Folders
#### Compile
Contains the `compile.compile` function.  
  
#### fixes
Contains all of the fixes generated by the `lib.run_test` function.  

#### html 
Contains all html files to test. Must only contain html files. One for each project under test.  

#### output
The result of the `compile.compile` function. Each subfolder is related to each prompting algorithm folder. Each json file in the subfolder correlates to an html file under test. It puts together multiple objects from various files so some information is redundant. It uses the following JSON schema:
```json
[
    {
        // Correlates to wgca_errors.json data
        "guideline": "", // The guideline number tested
        "success_criteria": "", // Short description of the guideline
        "examples": [ { "problem": "", "solution": "" } ], // Examples of the error and how it would be fixed

        // Correlates to violations.json
        "problem": {
            "guideline": "", // Should correlate to guideline id above
            "line": "", // Line number of violation
            "problem": "" // Text of supplied line (not found in violations.json but computed from it)
        },

        // correlates to fixes folder data
        "closest_fix": {
            "problem_type": "", // ChatGPT generated description of the error it found
            "offending_line": "", // line of html as it appears in the html folder
            "fixed_line": "" // line above fixed according to the guideline
        }
    },
    ...
]
```

#### t_1_No_Context
The control of the experiment. No guidance or context is given to the model except for the html of the project.  
**Example chat:**
```
System:
You will help fix accessability issues for a website.
You will be given the html for the website.
Your job is to find accessability related problems according to the WCAG guidelines.
You will return the line that has a problem, say what the problem is, and generate html that will fix the problem.
You will only return valid JSON according to this schema:
{
	"problem_type": "",
	"offending_line": "",
	"fixed_line": ""
}

User:
Here is the html for the page:
{contents of html file}

Assistant:
Ok

User:
Find the problem

Assistant:
{
    "problem_type": "missing_alt_attribute",
    "offending_line": "<img src="logo.png">",
    "fixed_line": "<img src="logo.png" alt="Website Logo">"
}
```

#### t_2_Guidance
Reference: Self-Instruct https://arxiv.org/pdf/2212.10560  
ChatGPT is given a description of a WCGA error to look for.  
**Example Chat:**  
```
System:
You will help fix accessability issues for a website.
You will be given the html for the website and a specific problem to look for.
Your job is to find an accessability related problem according to the rule given.
You will return the line that has a problem, say what the problem is, and generate html that will fix the problem.
You will only return valid JSON according to this schema:
{
	"problem_type": "", // Short description
	"offending_line": "", // one or more lines with the problem
	"fixed_line": "" // Fixed line or lines
}
If no error is found write "NONE" in the problem type property.

User:
Here is the html for the page:
{contents of html file}

Assistant:
Ok

User:
This is the type of problem: input element or button is missing an associated label, it contains an alt attribute, or its label is empty

Assistant:
Ok

User:
Find the problem

Assistant:
{
    "problem_type": "missing_alt_attribute",
    "offending_line": "<img src="logo.png">",
    "fixed_line": "<img src="logo.png" alt="Website Logo">"
}
```

#### t_3_Few_Shot
Reference: Language Models are Few Shot Learners https://proceedings.neurips.cc/paper_files/paper/2020/file/1457c0d6bfcb4967418bfb8ac142f64a-Paper.pdf  
Uses a few shot approach to give examples of this type of error being fixed.  
**Example Chat:**
```
System:
You will help fix accessability issues for a website.
You will be given the html for the website and a specific problem to look for.
Your job is to find an accessability related problem according to the rule given.
You will return the line that has a problem, say what the problem is, and generate html that will fix the problem.
You will only return valid JSON according to this schema:
{
	"problem_type": "", // Short description
	"offending_line": "", // one or more lines with the problem
	"fixed_line": "" // Fixed line or lines
}
If no error is found write "NONE" in the problem type property.

User:
Here is the html for the page:
{contents of html file}

Assistant:
Ok

User:
This is the type of problem: input element or button is missing an associated label, it contains an alt attribute, or its label is empty

Assistant:
Ok

User:
This is an example of the problem: <input type="file" id="myfile" name="myfile">

This is a possible solution: <label for="myfile">File</label><br>n<input type="file" id="myfile" name="myfile">

User:
Find the problem

Assistant:
{
    "problem_type": "missing_alt_attribute",
    "offending_line": "<img src="logo.png">",
    "fixed_line": "<img src="logo.png" alt="Website Logo">"
}
```

#### t_4_CoT
Reference: Chain of Thought https://proceedings.neurips.cc/paper_files/paper/2022/file/9d5609613524ecf4f15af0f7b31abca4-Paper-Conference.pdf  
Uses chain of thought to allow the model to think before it creates an output.  
**Example Chat:**
```
System:
You will help fix accessability issues for a website.
You will be given the html for the website and a specific problem to look for.
Your job is to find an accessability related problem according to the rule given.

User:
Here is the html for the page:
{contents of html file}

Assistant:
Ok

User:
This is the type of problem: input element or button is missing an associated label, it contains an alt attribute, or its label is empty

Assistant:
Ok

User:
Think through finding the problem step by step

Assistant:
{CoT output}

User:
You will return the line that has a problem, say what the problem is, and generate html that will fix the problem.
You will only return valid JSON according to this schema:
{
	"problem_type": "", // Short description
	"offending_line": "", // one or more lines with the problem
	"fixed_line": "" // Fixed line or lines
}
If no error is found write "NONE" in the problem type property.

Assistant:
{
    "problem_type": "missing_alt_attribute",
    "offending_line": "<img src="logo.png">",
    "fixed_line": "<img src="logo.png" alt="Website Logo">"
}
```

#### t_5_ToT
Reference: Tree of Thought https://arxiv.org/abs/2305.10601  
Uses the Tree of Thought algorithm to create multiple outputs and picks the best one.  
See paper and `ToT` class for further reference.