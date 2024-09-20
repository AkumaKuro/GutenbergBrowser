import json
import numpy as np
import requests
from bs4 import BeautifulSoup

class DatabaseUpdater:
  """A class solely used to separate updating logic from query logic,
  as to make the code more understandable. It is not meant to be used
  outside of the Database class below."""
  
  #The base url needed to collect all titles from gutenberg
  gutenberg_url = "https://www.gutenberg.org/browse/titles/"

  def get_all_titles(self):
    """This function collects all titles from Gutenberg"""
    letters = "abcdefghijklmnopqrstuvwxyz"
    all_titles = {}
    #Simply calls get_titles with each letter in the alphabet
    for letter in letters:
      titles = self.get_titles(letter)
      all_titles.update(titles)
    #Returns the complete list of all titles
    return all_titles

  def get_titles(self, letter):
    """Updates the list with all books starting with letter in their title"""
    titles = {}

    #Request data from Gutenberg
    site_data = requests.get(DatabaseUpdater.gutenberg_url + letter)
    if not site_data.status_code == 200:
      return titles
    data = BeautifulSoup(site_data.content, "html.parser")
    #Find all containers that hold the book data
    data = data.find_all("h2")
    #Go through all book titles from the previous containers
    for entry in data:
      #Skip this book if it is not english
      if "(English)" not in entry.text:
        continue
      #Extract the book title and the reference link to the book's files 
      book_data = entry.find("a")
      book_name = book_data.text
      book_source = book_data["href"]
      book_source = book_source.split("/")[-1]
      #Store both informations in the dictionary, source paired with title
      titles[book_name] = book_source
    return titles
    


class DataBase:
  """This class fetches information from the Gutenberg Project (gutenberg.org) and
  searches through the books for a book the user is searching for"""
  
  database_path = "./GutenBerg.db"
  book_url = "https://www.gutenberg.org/files/"
  
  def __init__(self):
    #Initializes all variables needed by this class to work with the data
    self.books = {}
    self.last_read = ""
    #Loads all data from storage into memory
    self.load()

  def update(self):
    """Collects all titles from Gutenberg and stores them in storage"""
    #Get all titles from the updater class
    updater = DatabaseUpdater()
    update = updater.get_all_titles()
    #Replace the old titles by the new ones
    self.books = update
    #Save the new data on the storage file
    self.save_data()

  def save_data(self):
    """Saves the current state of the program in storage, alongside
    any information about titles and their source urls"""
    #Construct a dictionary containing anything that needs to be saved
    #Could be expanded further in case more things need to be stored.
    data = {}
    data["last_read"] = self.last_read
    data["books"] = self.books
    #Store the python dictionary as a json object in GutenBerg.db
    #It is a json, but it uses a different extension to discourage
    #opening the file like a normal json
    with open(DataBase.database_path, "w") as database_file:
      json.dump(data, database_file)

  def load(self):
    """Loads the database data from storage into memory"""
    #Try opening the file
    try:
      with open(DataBase.database_path, "r") as database_file:
        database_data = json.load(database_file)
        #Assigns the loaded data to the local variables of the Database
        self.last_read = database_data["last_read"]
        self.books = database_data["books"]
        database_file.close()
    except:
      #If opening the file is not possible, because maybe it was not already created, skip the loading step and start with a blank database
      #Force an update for the program to work correctly
      print("No database could be found. Update required")
      print("Currently updating, please wait...")
      self.update()

  def get_last_read(self):
    """A getter function to retrieve the book title that was selected
    last time the program was run"""
    return self.last_read

  def find_similarity(self, title1, title2):
    """This function searches for the Levenshtein distance between two
    titles, which can be used to search for similar titles"""
    #Turn the strings into lists of letters
    title1 = [symbol for symbol in title1.lower()]
    title2 = [symbol for symbol in title2.lower()]
    
    #Initializing the result matrix
    res = np.zeros((len(title2), len(title1)))
    
    #Defining the borders of the matrix to be the length of the strings
    res[0] = [i for i in range(len(title1))]
    res[:,0] = [i for i in range(len(title2))]

    #Iterate through the lists, calculating the Levenshtein distance
    #Please refer to the link below for a more detailed explanation
    #https://blog.paperspace.com/measuring-text-similarity-using-levenshtein-distance/
    for y in range(1, len(title1)):
        for x in range(1, len(title2)):
            
            if title2[x] != title1[y]:
                res[x, y] = min(res[x - 1, y], res[x, y - 1]) + 1
            
            else:
                res[x, y] = res[x - 1, y - 1]
    string_distance = int(res[-1, -1])
    #Returns the distance between the two strings. The higher, the more different they are
    return string_distance

  def get_possible_titles(self, user_book_title, title_limit = 5):
    """Takes a book title from the user and returns n-amount of titles
    that match the input closest, with n being the title_limit"""
    title_similarity = []

    #For every title in the database, check for similarity to the searched title
    #Note that the higher the similarity-count, the less similar they are
    for title in self.books.keys():
      #Find the similarity, pair it with the title, and append to the list
      similarity = self.find_similarity(title, user_book_title)
      title_pair = (similarity, title)
      title_similarity.append(title_pair)
      #Since we only need n books, we remove the least fitting titles after n titles
      if len(title_similarity) > title_limit:
        title_similarity.remove(max(title_similarity))

    #Using the similarity of titles, return a list of n possible titles
    possible_titles = []
    #Put the titles in order, with most likely being the first
    title_similarity.sort()
    for entry in title_similarity:
      #Store only the title, the similarity measurement is not needed now
      possible_titles.append(entry[1])
    #Return the list of titles
    return possible_titles

  def set_last_read(self, title):
    """A helper function to store the last read book from the user"""
    self.last_read = title
    #Simply uses the function to store the entire state of the object
    #As mentioned above
    self.save_data()

  def open_book(self, title):
    """This function takes a book title and returns the books url,
    if the title is contained within the database. Returns whether
    it succeeded or not"""

    #If the book was not found in the database, prompts the user
    #To update it and try it again
    if not title in self.books:
      print("Looks like there was a problem opening the book")
      print("Please update the program and try it again")
      return False
    
    #Construct a link to the title's files
    book_source = self.books[title]
    title_url = DataBase.book_url + book_source
    
    book_file_data = requests.get(title_url)
    #If the program did not successfully find a link, it stops the function
    if book_file_data.status_code != 200:
      return False

    #Extract all possible file versions of the book
    book_files = BeautifulSoup(book_file_data.content, "html.parser")
    book_files = book_files.find_all("tr")
    book_file_path = ""
    #Loop through the possible versions and select .txt
    for book_file in book_files:
      book_file = book_file.find("a")
      if book_file:
        book_file = book_file["href"]
        #If it finds a text file, select that file and end the loop
        if ".txt" in book_file:
          book_file_path = book_file
          break

    #If no text file was found, exit the function with a prompt to the user
    if not book_file_path:
      print("Unable to find a file for the book")
      return False
          
    book_file_path = title_url + "/" + book_file_path    
        

    #Return the book's link to the user
    print(book_file_path)
    return True



    
#This is where the actual program starts
    
#Initialize the database
database = DataBase()

def ask_question(question):
  """A function that asks the user a question. If the answer is part
  of the possible responses, returns true, else false"""
  #Possible responses, caps are ignored
  responses = ["yes", "yeah", "y"]
  #Ask the question
  user_response = input(question + " [y/n]\n")
  user_answer = False
  #If the answer (with caps ignored) is possible, return true
  if user_response.lower() in responses:
    user_answer = True
  #Else return false
  return user_answer

def update_database():
  """Asks the user if they want to update the program's database"""

  #Ask whether to update or not
  question = "Do you want to update the database?"
  answer = ask_question(question)
  #If they respond with yes, update it, if not, skip the update
  if answer == True:
    print("Alright, then please stay patient, this can take a while...")
    database.update()
    print("Update finished!" + "\n" * 3)


def present_last_read():
  """If the user has read a book last time, it will ask the user,
  whether they want to reopen that book again or not"""
  #Retrieve the last read book title
  book_title = database.get_last_read()
  #If the user has never read a book before, do not ask
  if not book_title:
    return False, ""
  #If there is a book last read, present it
  print("\nLast time, you read \"{}\"".format(book_title))
  #Ask if they want to read that book
  question = "Do you want to continue reading?"
  answer = ask_question(question)
  #Return the answer and the book title
  return answer, book_title


def main():
  book_title = ""
  
  #Ask user if they want to update the database
  update_database()
  
  #If user read a book before, ask if they want to continue reading
  last_read, book_title = present_last_read()
  if last_read:
    #If they agree to continue, present the link and exit the loop
    print("You will now start reading {}. Have fun!".format(book_title))
    database.open_book(book_title)
    return True
    
  #If not, ask user what book title they want to search for
  print("\nPlease enter the name of a book you want to read:")
  user_book_title = input("Book Title: ")
  print("\nAlright, currently searching through the library, please wait...")
  #Search for possible book titles the user could refer to
  possible_titles = database.get_possible_titles(user_book_title)

  #Show user possible results, ask which one of them
  print("\nFound following book titles based on your search. Choose one:")
  #Present the selection of possible book titles
  index = 1
  for possible_title in possible_titles:
    print("{}. {}".format(str(index), possible_title))
    index += 1
  #Ask which of the books the user was refering to
  selected_id = input("Please select the books ID: ")
  try:
    #Choose the selected title from the array using the provided ID
    selected_id = int(selected_id)
    book_title = possible_titles[selected_id - 1]
  except:
    #If the ID is not valid, terminate the program
    print("Error. That ID is not valid.")
    return False

  #Present the link, and exit the loop
  print("You will now start reading {}. Have fun!".format(book_title))
  #Since this is now the last read book, store it in the database
  database.set_last_read(book_title)
  #If the link could not be constructed, the loop starts again
  succeeded = database.open_book(book_title)
  if not succeeded:
    #Prompt the user if the book link was not able to be queried
    print("There seems to be a problem. Make sure you are connected to the internet.")
  return succeeded


#If this program is run by itself, it starts the main-loop
#If the program was only imported, it will not start the main-loop
if __name__ == "__main__":
  reads_book = False
  #As long as no book was properly selected, repeat the loop
  while not reads_book:
    print("\n" * 3)
    #The main function returns whether the search succeeded or not
    try:
      reads_book = main()
    except:
      #If any errors occure, notify the user and restart the program
      print("Something went wrong, please try again")
      print("Make sure to update the program, and that you are connected to the internet")
      continue