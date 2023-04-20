import openai
import json
import subprocess
import os

with open("config.json", "r") as f:
	config = json.load(f)

context = []
commands = []

End = False
firstRun = True
manualMode = False

def getKey(config):
	return config["API_KEY"]
	
def getSystemPrompt(config):
	return config["SYSTEM_PROMPT"]
	
def storeSystemPrompt():
	systemPrompt = getSystemPrompt(config)
	promptStore = {"role": "system", "content": systemPrompt}
	context.append(promptStore)

def saveCurrentPrompt(prompt):
	promptStore = {"role": "user", "content": prompt}
	context.append(promptStore)

def saveLastResponse(response):
	responseStore = {"role": "assistant", "content": response}
	context.append(responseStore)
	
def saveLastCommand(response, commands):
	for line in response.splitlines():
		if line.startswith("BSH: "):
			command = line[5:]
			commands.append(command)
		elif line.startswith("BSH "):
			command = line[4:]
			commands.append(command)

def getResponse(context):
	openai.api_key = getKey(config)
	reply = openai.ChatCompletion.create(model="gpt-4", messages=context)
	response = reply['choices'][0]['message']['content']
	print("\n"+response)
	saveLastResponse(response)
	saveLastCommand(response, commands)
	
def getLastCommand(commands):
	return commands[-1]
	
def getPrompt(command):
	try:
		result = subprocess.run(command, check=True, shell=True, timeout=180, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	except subprocess.CalledProcessError as err:
		output = str(err)
	except subprocess.TimeoutExpired as err:
		output = "Command timed out"
	else:
		output = str(result.stdout.decode("utf-8"))
	print("\n"+output)
	saveCurrentPrompt(output)
	
def setPrompt():
	with open("manual.txt", "r") as f:
		manualPrompt = f.read()
	print(manualPrompt)
	saveCurrentPrompt(manualPrompt)
	
def getInitialPrompt():
	initialPrompt = ""
	start = config["MAIN_START_PROMPT"]
	pastResults = config["PAST_RESULTS"]
	pastMethods = config["PAST_METHODS"]
	if len(pastResults) > 0:
		initialPrompt = initialPrompt + f"Results of past scans, no need to repeat these scans: {pastResults}\n\n"
	if len(pastMethods) > 0:
		initalPrompt = initialPrompt + f"Test has already been completed using {pastMethods}. Please try alternative methods in this next test.\n\n"
	initialPrompt = initalPrompt + start
	
	return initialPrompt
	
def saveContextToMemory():
	with open("context.txt", "w+") as f:
		f.write(str(context)+"\n"+str(commands))
		
storeSystemPrompt()

while not End:
	if firstRun:
		if os.path.isfile("context.txt"):
			with open("context.txt", "r") as f:
				print("Resuming previous chat...")
				lists = f.splitlines()
				context = lists[0]
				commands = lists[1]
			os.remove("context.txt")
		else:
			saveCurrentPrompt(getInitialPrompt())
	elif manualMode:
		setPrompt()
		manualMode = False
	else:
		getPrompt(getLastCommand(commands))
	firstRun = False
	try:
		getResponse(context)
	except openai.error.RateLimitError:
		print("\n Request to GPT-4 timed out, storing chat context")
		saveContextToMemory()
	print("\nPress enter to continue, type m to enter manual prompt mode, type q to quit")
	loop = input("Proceed to next stage? ")
	if loop == "":
		End = False
	elif loop == "m":
		manualMode = True
	else:
		End = True
