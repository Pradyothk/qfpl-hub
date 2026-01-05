import streamlit as st
import pandas as pd
import requests
import re
import io
import time

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="QFPL Hub",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- EMBEDDED DATA ---
CSV_LINEUPS = """TEAM,PLAYER,TEAM,1,2,3,4,5,6,7
ARS,Arya Jain,ARS,S,S,S,C,,,
ARS,Dev Parikh,ARS,C,S,B,B,,,
ARS,Gaurav Gharge,ARS,S,S,B,S,,,
ARS,George Anagnostou,ARS,S,S,C,B,,,
ARS,Preet Chheda,ARS,S,B,S,S,,,
ARS,Preet Dedhia,ARS,S,B,S,S,,,
ARS,Saahil Sawant,ARS,B,B,S,S,,,
ARS,Shaad Lakdawala,ARS,B,S,B,S,,,
ARS,Shahmoon Ali Shah,ARS,B,C,S,B,,,
ARS,Tanuj Baru,ARS,B,B,S,S,,,
ARS,Timothy Leichtfried,ARS,S,S,B,B,,,
AVL,Abhiyank Choudhary,AVL,S,B,B,S,,,
AVL,Aditya Khullar,AVL,S,S,S,B,,,
AVL,Anson Rodrigues,AVL,S,S,B,B,,,
AVL,Avishek Das,AVL,B,C,S,S,,,
AVL,Darshil Shastri,AVL,S,S,B,B,,,
AVL,Debarun Guha,AVL,S,B,B,S,,,
AVL,Piyush Nathani,AVL,B,B,S,C,,,
AVL,Rishi Gehi,AVL,B,S,S,S,,,
AVL,Sagar Reddy,AVL,B,S,S,B,,,
AVL,Sarbik Dutta,AVL,C,S,S,S,,,
AVL,Sidharth Jain,AVL,S,B,C,S,,,
BOU,Akhil D,BOU,S,S,S,S,,,
BOU,Akshay Bhat,BOU,S,S,B,S,,,
BOU,Akshay Surve,BOU,B,C,S,B,,,
BOU,James Buller,BOU,C,B,S,B,,,
BOU,Kiran Kelkar,BOU,B,S,B,B,,,
BOU,Parth Mau,BOU,S,S,B,S,,,
BOU,Projwal Deb,BOU,B,S,S,B,,,
BOU,Rohit Ravi,BOU,B,B,S,S,,,
BOU,Vineet Udeshi,BOU,S,B,B,C,,,
BOU,Viral Panchal,BOU,S,B,S,S,,,
BOU,Vishnu Bhargav Janga,BOU,S,S,C,S,,,
BRE,Adit Maniktala,BRE,B,S,B,S,,,
BRE,Aman Arora,BRE,S,S,C,S,,,
BRE,Ashish Sharma,BRE,B,B,S,S,,,
BRE,Chandranil Mazumdar,BRE,S,B,S,C,,,
BRE,Harshal Bhungavale,BRE,S,B,B,S,,,
BRE,Mihir Pandya,BRE,S,C,S,B,,,
BRE,Mihir Ranade,BRE,B,S,S,B,,,
BRE,Mohar Moghe,BRE,S,S,B,S,,,
BRE,Rahul Vasu,BRE,B,S,B,S,,,
BRE,Siddharth Shenoy,BRE,S,S,S,B,,,
BRE,Umang Shah,BRE,C,B,S,B,,,
BHA,Abeen Bhattacharya,BHA,S,B,B,C,,,
BHA,Aditya Kalra,BHA,S,S,S,S,,,
BHA,Animesh Srivastava,BHA,B,S,S,B,,,
BHA,Anubhav Agarwal,BHA,S,B,S,B,,,
BHA,Harsh Ranjan,BHA,B,B,S,B,,,
BHA,Onas Malhotra,BHA,S,C,B,S,,,
BHA,Oni Malhotra,BHA,S,S,C,S,,,
BHA,Raghav Daga,BHA,C,S,B,B,,,
BHA,Shantanu Jha,BHA,B,B,S,S,,,
BHA,Swastik Dhopte,BHA,S,S,B,S,,,
BHA,Vivek Yadav,BHA,B,S,S,S,,,
BUR,Alissa Dsouza,BUR,S,B,S,C,,,
BUR,Amee Kapadia,BUR,B,S,S,B,,,
BUR,Anurag Khetan,BUR,B,S,S,S,,,
BUR,Delzad Bajan,BUR,S,S,B,S,,,
BUR,Jasprit Singh Sudan,BUR,C,S,B,S,,,
BUR,Rohan Ghosh,BUR,S,B,C,B,,,
BUR,Rudra Joshi,BUR,S,B,S,B,,,
BUR,Siddharth Nachankar,BUR,S,B,S,S,,,
BUR,Sidharth Nandwani,BUR,S,S,B,B,,,
BUR,Stefan Amanna,BUR,B,S,S,S,,,
BUR,Vaastav Anand,BUR,B,C,B,S,,,
CHE,Aarsh Mehta,CHE,C,S,B,S,,,
CHE,Abhigyan Khargharia,CHE,B,B,S,S,,,
CHE,Akshay Kumar,CHE,S,S,B,S,,,
CHE,Gaurab Kar,CHE,B,B,S,S,,,
CHE,Jay Shah,CHE,B,S,S,B,,,
CHE,Jay Vora,CHE,S,C,S,S,,,
CHE,Kowshik Suriyanarayanan,CHE,S,S,B,B,,,
CHE,Sushil Jadhav,CHE,S,B,C,S,,,
CHE,Varun Kumar,CHE,S,S,S,B,,,
CHE,Vishal Ananthakrishnan,CHE,S,S,B,B,,,
CHE,Vivek Merchant,CHE,B,B,S,C,,,
CRY,Adam Boustani,CRY,B,S,S,B,,,
CRY,Angelo Schellens,CRY,S,B,S,B,,,
CRY,Anshuman Dhanorkar,CRY,S,S,S,B,,,
CRY,Atinder Singh,CRY,S,S,B,C,,,
CRY,Maxilio John D'souza,CRY,B,C,B,S,,,
CRY,Mayur Bhatia,CRY,S,B,S,S,,,
CRY,Mayur Mishra,CRY,B,S,C,B,,,
CRY,Morrinho Pereira,CRY,B,S,B,S,,,
CRY,Rasendra Gaitonde,CRY,S,S,B,S,,,
CRY,Rohan Singhvi,CRY,C,B,S,S,,,
CRY,Shahbaz Anwer,CRY,S,B,S,S,,,
EVE,Amnay Sheel Khosla,EVE,B,S,B,B,,,
EVE,Dhruv Prasad,EVE,S,C,B,B,,,
EVE,Divyank Sharma,EVE,S,S,C,S,,,
EVE,Gaurav Partap Singh,EVE,S,B,B,S,,,
EVE,Kshitij Pandey,EVE,S,B,B,S,,,
EVE,Nikhil Narain,EVE,C,B,S,S,,,
EVE,Nilesh Agrawal,EVE,B,S,S,S,,,
EVE,Raghav Nath,EVE,S,S,S,B,,,
EVE,Sodaksh Khullar,EVE,B,B,S,B,,,
EVE,Somnath Dey,EVE,B,S,S,C,,,
EVE,Uddhav Prasad,EVE,S,S,S,S,,,
FUL,Arvind Mahesh,FUL,S,S,S,S,,,
FUL,Bharath Ravichandran,FUL,B,S,B,S,,,
FUL,Gandhar Badle,FUL,B,B,S,C,,,
FUL,Gurdit Singh Lugani,FUL,S,B,C,S,,,
FUL,Jai Kumar,FUL,B,S,S,S,,,
FUL,Karthik Easwar Elangovan,FUL,B,S,S,B,,,
FUL,Lv Shukla,FUL,C,B,S,B,,,
FUL,Pradyoth Kalavagunta,FUL,S,C,B,S,,,
FUL,Ramkumar Ananthakrishnan,FUL,S,B,S,B,,,
FUL,Surya Raman,FUL,S,S,B,B,,,
FUL,Vibudh Dixit,FUL,S,S,B,S,,,
LEE,Abhishek Pande,LEE,B,S,S,S,,,
LEE,Aliasgar Badami,LEE,B,B,S,B,,,
LEE,Haider Sayyed,LEE,S,B,B,S,,,
LEE,Jash Mehta,LEE,S,C,B,S,,,
LEE,Jay Lokegaonkar,LEE,B,S,B,C,,,
LEE,Muzzammil Peerbhai,LEE,C,S,S,S,,,
LEE,Ravi Jalan,LEE,S,B,S,B,,,
LEE,Sahil Bapat,LEE,S,B,S,S,,,
LEE,Shahid Nabi,LEE,S,S,S,S,,,
LEE,Siddharth Thakur,LEE,S,S,C,B,,,
LEE,Suraj Janyani,LEE,B,S,B,B,,,
LIV,Ajeesh VR,LIV,S,S,S,B,,,
LIV,Akshar,LIV,B,C,S,B,,,
LIV,Dhruv Kapur,LIV,B,B,S,C,,,
LIV,Navez Khan,LIV,B,S,S,S,,,
LIV,Prathmesh Rangari,LIV,B,B,S,S,,,
LIV,Rishabh Kothari,LIV,S,S,B,S,,,
LIV,Rishav Das,LIV,S,B,S,S,,,
LIV,Sanjeev Rai,LIV,S,B,C,S,,,
LIV,Shefal Chirawawala,LIV,S,S,B,B,,,
LIV,Varun S. Ranipeta,LIV,S,S,B,S,,,
LIV,Zubin Sheriar,LIV,C,S,B,B,,,
MCI,Abhimanyu Choudhury,MCI,C,B,B,S,,,
MCI,Abhinav Singh Sidhu,MCI,S,S,S,B,,,
MCI,Anirudh Shenoy,MCI,S,S,S,S,,,
MCI,Gokul Krishna,MCI,B,S,S,B,,,
MCI,Krishna Zanwar,MCI,B,C,B,S,,,
MCI,Nidhin Mathews,MCI,S,B,S,B,,,
MCI,Prathmesh Kocheta,MCI,S,B,B,C,,,
MCI,Raghav L Narasimhan,MCI,B,S,B,S,,,
MCI,Samson Baretto,MCI,S,S,S,B,,,
MCI,Saran Prasanth,MCI,S,B,S,S,,,
MCI,Sriram Ranganath,MCI,B,S,C,S,,,
MUN,Aaryan Rathi,MUN,S,B,B,C,,,
MUN,Ankur Mokal,MUN,S,C,S,S,,,
MUN,Anugreh Kumar,MUN,B,S,S,S,,,
MUN,Anuj Chandna,MUN,B,S,S,B,,,
MUN,Arijit Deb,MUN,S,S,B,B,,,
MUN,Lakshmi Narayanan,MUN,B,B,S,B,,,
MUN,Rahul Bhatu,MUN,B,S,B,B,,,
MUN,Rohan Singh,MUN,S,S,S,S,,,
MUN,Sheeraj Sengupta,MUN,S,B,S,S,,,
MUN,Utsav Ojha,MUN,C,B,B,S,,,
MUN,Yatin Mehra,MUN,S,S,C,S,,,
NEW,Akshat Jain,NEW,S,C,B,S,,,
NEW,Amitabh Agrawal,NEW,B,S,S,B,,,
NEW,Kinnari Vyas,NEW,B,S,B,S,,,
NEW,Piotr Kolodziej,NEW,S,S,S,S,,,
NEW,Prabhav VD,NEW,S,B,S,B,,,
NEW,Rahul VN,NEW,S,B,C,S,,,
NEW,Saswat Mishra,NEW,S,S,B,B,,,
NEW,Shashwat Mehrotra,NEW,B,S,B,S,,,
NEW,Siddharth Shinde,NEW,C,S,S,S,,,
NEW,Upamanyu Modukuru,NEW,B,B,S,C,,,
NEW,Vishnu Rajesh,NEW,S,B,S,B,,,
NFO,Ankur Goyal,NFO,S,S,C,S,,,
NFO,Arun Goyal,NFO,S,S,B,S,,,
NFO,Jay Bansal,NFO,S,B,B,S,,,
NFO,Prarabdh Chaturvedi,NFO,B,C,S,S,,,
NFO,Reuben Sam,NFO,B,B,S,B,,,
NFO,Shashank Jha,NFO,B,B,S,S,,,
NFO,Shiromi Chaturvedi,NFO,C,S,B,B,,,
NFO,Shubham Choudhary,NFO,S,S,S,B,,,
NFO,Soham Ghosh,NFO,B,S,S,S,,,
NFO,Swaroop Sarkar,NFO,S,S,B,C,,,
NFO,Vignesh Rajan,NFO,S,B,S,B,,,
SUN,Ajinkya Kale,SUN,B,S,C,B,,,
SUN,Avtansh Behal,SUN,S,B,S,S,,,
SUN,Ayanjit Chattopadhyay,SUN,S,B,S,C,,,
SUN,Kunal Soni,SUN,S,S,S,B,,,
SUN,Mohit Pant,SUN,S,S,B,S,,,
SUN,Priyan Gada,SUN,B,C,B,B,,,
SUN,Rajan Valecha,SUN,S,B,S,B,,,
SUN,Sanjay Krishna,SUN,B,S,S,S,,,
SUN,Snehasis Panda,SUN,C,B,B,S,,,
SUN,Sukhmani Singh,SUN,S,S,B,S,,,
SUN,Vishwa Jatania,SUN,B,S,S,S,,,
TOT,Aniket Neogi,TOT,B,S,B,C,,,
TOT,Aritra Mitra,TOT,S,S,B,S,,,
TOT,Ashwin Menon,TOT,S,B,S,B,,,
TOT,Kunal Bhatia,TOT,S,B,S,S,,,
TOT,Manan Vyas,TOT,C,B,S,S,,,
TOT,Mihir Vahi,TOT,B,S,C,B,,,
TOT,Pranav Mhatre,TOT,S,C,B,S,,,
TOT,Rahi Reza,TOT,B,B,S,S,,,
TOT,Ritobrata Nath,TOT,S,S,S,B,,,
TOT,Rohan Parekh,TOT,B,S,S,B,,,
TOT,Saksham Agarwal,TOT,S,S,B,S,,,
WHU,Advait Keswani,WHU,S,S,C,B,,,
WHU,Angad Singh,WHU,S,B,S,B,,,
WHU,Bhavika Anand,WHU,B,S,S,B,,,
WHU,Divij Ohri,WHU,S,C,B,S,,,
WHU,Harsh Rathod,WHU,S,S,S,S,,,
WHU,Jimmit Mehta,WHU,S,S,S,C,,,
WHU,Rujan Borges,WHU,S,B,B,S,,,
WHU,Sachin Omprakash,WHU,C,B,B,S,,,
WHU,Samarth Makhija,WHU,B,S,B,S,,,
WHU,Sreeradh RP,WHU,B,S,S,S,,,
WHU,Sriram Srinivasan,WHU,B,B,S,B,,,
WOL,Aksh Kapoor,WOL,S,B,S,B,,,
WOL,Gilson Rafael,WOL,S,S,B,S,,,
WOL,Hisham Ashraf,WOL,S,S,S,S,,,
WOL,Karan Manik,WOL,S,B,S,B,,,
WOL,Kashyap Reddy,WOL,B,S,B,C,,,
WOL,Kevin Sequeira,WOL,B,B,S,S,,,
WOL,Santosh Krishna,WOL,C,S,S,B,,,
WOL,Shekhar Perugu,WOL,S,S,C,S,,,
WOL,Sreekanth Reddy,WOL,S,B,S,S,,,
WOL,Vysakh Murali,WOL,B,C,B,S,,,
WOL,Yasser Rajwani,WOL,B,S,B,B,,,
"""

CSV_REGISTRATIONS = """Player,Profile
Jaidev Tripathy,https://fantasy.premierleague.com/entry/2395259/history
Jignesh Shah,https://fantasy.premierleague.com/entry/6472/history
Saurabh Wakode,https://fantasy.premierleague.com/entry/1158412/history
Simraan Panwar,https://fantasy.premierleague.com/entry/88361/history
Sumedh Garge,https://fantasy.premierleague.com/entry/226183/history
Udbhav Saha,https://fantasy.premierleague.com/entry/59794/history
Dhawal Lachhwani,https://fantasy.premierleague.com/entry/6980704/history
Daksha Iyer,https://fantasy.premierleague.com/entry/3729344/history
Saksham Arora,https://fantasy.premierleague.com/entry/2408693/history
Tanveer Singh,https://fantasy.premierleague.com/entry/4264/history
Arya Jain,https://fantasy.premierleague.com/entry/1221824/history
Dev Parikh,https://fantasy.premierleague.com/entry/25216/history
Gaurav Gharge,https://fantasy.premierleague.com/entry/13035/history
George Anagnostou,https://fantasy.premierleague.com/entry/11432/history
Preet Chheda,https://fantasy.premierleague.com/entry/478000/history
Preet Dedhia,https://fantasy.premierleague.com/entry/388983/history
Saahil Sawant,https://fantasy.premierleague.com/entry/4805767/history
Shaad Lakdawala,https://fantasy.premierleague.com/entry/82826/history
Shahmoon Ali Shah,https://fantasy.premierleague.com/entry/6003993/history
Tanuj Baru,https://fantasy.premierleague.com/entry/517401/history
Timothy Leichtfried,https://fantasy.premierleague.com/entry/97919/history
Abhiyank Choudhary,https://fantasy.premierleague.com/entry/12177/history
Aditya Khullar,https://fantasy.premierleague.com/entry/2411708/history
Anson Rodrigues,https://fantasy.premierleague.com/entry/4949507/history
Avishek Das,https://fantasy.premierleague.com/entry/20696/history
Darshil Shastri,https://fantasy.premierleague.com/entry/2123716/history
Debarun Guha,https://fantasy.premierleague.com/entry/10735/history
Piyush Nathani,https://fantasy.premierleague.com/entry/102225/history
Rishi Gehi,https://fantasy.premierleague.com/entry/17807/history
Sagar Reddy,https://fantasy.premierleague.com/entry/14059/history
Sarbik Dutta,https://fantasy.premierleague.com/entry/15515/history
Sidharth Jain,https://fantasy.premierleague.com/entry/11606/history
Akhil D,https://fantasy.premierleague.com/entry/43805/history
Akshay Bhat,https://fantasy.premierleague.com/entry/18604/history
Akshay Surve,https://fantasy.premierleague.com/entry/8287/history
James Buller,https://fantasy.premierleague.com/entry/47440/history
Kiran Kelkar,https://fantasy.premierleague.com/entry/52696/history
Parth Mau,https://fantasy.premierleague.com/entry/258145/history
Projwal Deb,https://fantasy.premierleague.com/entry/1661725/history
Rohit Ravi,https://fantasy.premierleague.com/entry/20159/history
Vineet Udeshi,https://fantasy.premierleague.com/entry/52860/history
Viral Panchal,https://fantasy.premierleague.com/entry/5679278/history
Vishnu Bhargav Janga,https://fantasy.premierleague.com/entry/23277/history
Adit Maniktala,https://fantasy.premierleague.com/entry/684711/history
Aman Arora,https://fantasy.premierleague.com/entry/15263/history
Ashish Sharma,https://fantasy.premierleague.com/entry/17924/history
Chandranil Mazumdar,https://fantasy.premierleague.com/entry/1004270/history
Harshal Bhungavale,https://fantasy.premierleague.com/entry/585313/history
Mihir Pandya,https://fantasy.premierleague.com/entry/3113/history
Mihir Ranade,https://fantasy.premierleague.com/entry/540994/history
Mohar Moghe,https://fantasy.premierleague.com/entry/155179/history
Rahul Vasu,https://fantasy.premierleague.com/entry/1385442/history
Siddharth Shenoy,https://fantasy.premierleague.com/entry/616635/history
Umang Shah,https://fantasy.premierleague.com/entry/33091/history
Abeen Bhattacharya,https://fantasy.premierleague.com/entry/284660/history
Aditya Kalra,https://fantasy.premierleague.com/entry/84713/history
Animesh Srivastava,https://fantasy.premierleague.com/entry/1025728/history
Anubhav Agarwal,https://fantasy.premierleague.com/entry/1696225/history
Harsh Ranjan,https://fantasy.premierleague.com/entry/8435808/history
Onas Malhotra,https://fantasy.premierleague.com/entry/5531280/history
Oni Malhotra,https://fantasy.premierleague.com/entry/5720051/history
Raghav Daga,https://fantasy.premierleague.com/entry/59430/history
Shantanu Jha,https://fantasy.premierleague.com/entry/4064159/history
Swastik Dhopte,https://fantasy.premierleague.com/entry/22241/history
Vivek Yadav,https://fantasy.premierleague.com/entry/457390/history
Alissa Dsouza,https://fantasy.premierleague.com/entry/20138/history
Amee Kapadia,https://fantasy.premierleague.com/entry/138917/history
Anurag Khetan,https://fantasy.premierleague.com/entry/717/history
Delzad Bajan,https://fantasy.premierleague.com/entry/533100/history
Jasprit Singh Sudan,https://fantasy.premierleague.com/entry/114747/history
Rohan Ghosh,https://fantasy.premierleague.com/entry/20125/history
Rudra Joshi,https://fantasy.premierleague.com/entry/1935169/history
Siddharth Nachankar,https://fantasy.premierleague.com/entry/59878/history
Sidharth Nandwani,https://fantasy.premierleague.com/entry/8023/history
Stefan Amanna,https://fantasy.premierleague.com/entry/5538/history
Vaastav Anand,https://fantasy.premierleague.com/entry/25600/history
Aarsh Mehta,https://fantasy.premierleague.com/entry/406181/history
Abhigyan Khargharia,https://fantasy.premierleague.com/entry/2348502/history
Akshay Kumar,https://fantasy.premierleague.com/entry/19690/history
Gaurab Kar,https://fantasy.premierleague.com/entry/582767/history
Jay Shah,https://fantasy.premierleague.com/entry/4601241/history
Jay Vora,https://fantasy.premierleague.com/entry/5527125/history
Kowshik Suriyanarayanan,https://fantasy.premierleague.com/entry/43814/history
Sushil Jadhav,https://fantasy.premierleague.com/entry/51278/history
Varun Kumar,https://fantasy.premierleague.com/entry/3475023/history
Vishal Ananthakrishnan,https://fantasy.premierleague.com/entry/1489728/history
Vivek Merchant,https://fantasy.premierleague.com/entry/5508577/history
Adam Boustani,https://fantasy.premierleague.com/entry/213/history
Angelo Schellens,https://fantasy.premierleague.com/entry/6293/history
Anshuman Dhanorkar,https://fantasy.premierleague.com/entry/2749549/history
Atinder Singh,https://fantasy.premierleague.com/entry/152104/history
Maxilio John D'souza,https://fantasy.premierleague.com/entry/5313/history
Mayur Bhatia,https://fantasy.premierleague.com/entry/261545/history
Mayur Mishra,https://fantasy.premierleague.com/entry/1369142/history
Morrinho Pereira,https://fantasy.premierleague.com/entry/415518/history
Rasendra Gaitonde,https://fantasy.premierleague.com/entry/676990/history
Rohan Singhvi,https://fantasy.premierleague.com/entry/1295/history
Shahbaz Anwer,https://fantasy.premierleague.com/entry/190195/history
Amnay Sheel Khosla,https://fantasy.premierleague.com/entry/4620665/history
Dhruv Prasad,https://fantasy.premierleague.com/entry/36206/history
Divyank Sharma,https://fantasy.premierleague.com/entry/20752/history
Gaurav Partap Singh,https://fantasy.premierleague.com/entry/380640/history
Kshitij Pandey,https://fantasy.premierleague.com/entry/118785/history
Nikhil Narain,https://fantasy.premierleague.com/entry/23896/history
Nilesh Agrawal,https://fantasy.premierleague.com/entry/7376251/history
Raghav Nath,https://fantasy.premierleague.com/entry/17267/history
Sodaksh Khullar,https://fantasy.premierleague.com/entry/7187173/history
Somnath Dey,https://fantasy.premierleague.com/entry/624342/history
Uddhav Prasad,https://fantasy.premierleague.com/entry/4623590/history
Arvind Mahesh,https://fantasy.premierleague.com/entry/582057/history
Bharath Ravichandran,https://fantasy.premierleague.com/entry/1176245/history
Gandhar Badle,https://fantasy.premierleague.com/entry/278608/history
Gurdit Singh Lugani,https://fantasy.premierleague.com/entry/2493619/history
Jai Kumar,https://fantasy.premierleague.com/entry/4518462/history
Karthik Easwar Elangovan,https://fantasy.premierleague.com/entry/20825/history
Lv Shukla,https://fantasy.premierleague.com/entry/14803/history
Pradyoth Kalavagunta,https://fantasy.premierleague.com/entry/7650/history
Ramkumar Ananthakrishnan,https://fantasy.premierleague.com/entry/331867/history
Surya Raman,https://fantasy.premierleague.com/entry/246433/history
Vibudh Dixit,https://fantasy.premierleague.com/entry/3447420/history
Abhishek Pande,https://fantasy.premierleague.com/entry/4597645/history
Aliasgar Badami,https://fantasy.premierleague.com/entry/3655696/history
Haider Sayyed,https://fantasy.premierleague.com/entry/3090420/history
Jash Mehta,https://fantasy.premierleague.com/entry/22127/history
Jay Lokegaonkar,https://fantasy.premierleague.com/entry/124380/history
Muzzammil Peerbhai,https://fantasy.premierleague.com/entry/335416/history
Ravi Jalan,https://fantasy.premierleague.com/entry/4318163/history
Sahil Bapat,https://fantasy.premierleague.com/entry/7165/history
Shahid Nabi,https://fantasy.premierleague.com/entry/5055362/history
Siddharth Thakur,https://fantasy.premierleague.com/entry/42966/history
Suraj Janyani,https://fantasy.premierleague.com/entry/397091/history
Ajeesh VR,https://fantasy.premierleague.com/entry/18276/history
Akshar,https://fantasy.premierleague.com/entry/423961/history
Dhruv Kapur,https://fantasy.premierleague.com/entry/5634833/history
Navez Khan,https://fantasy.premierleague.com/entry/1956257/history
Prathmesh Rangari,https://fantasy.premierleague.com/entry/897373/history
Rishabh Kothari,https://fantasy.premierleague.com/entry/824265/history
Rishav Das,https://fantasy.premierleague.com/entry/3564691/history
Sanjeev Rai,https://fantasy.premierleague.com/entry/89291/history
Shefal Chirawawala,https://fantasy.premierleague.com/entry/291367/history
Varun S. Ranipeta,https://fantasy.premierleague.com/entry/135398/history
Zubin Sheriar,https://fantasy.premierleague.com/entry/1093785/history
Abhimanyu Choudhury,https://fantasy.premierleague.com/entry/81424/history
Abhinav Singh Sidhu,https://fantasy.premierleague.com/entry/57382/history
Anirudh Shenoy,https://fantasy.premierleague.com/entry/23357/history
Gokul Krishna,https://fantasy.premierleague.com/entry/15772/history
Krishna Zanwar,https://fantasy.premierleague.com/entry/36717/history
Nidhin Mathews,https://fantasy.premierleague.com/entry/2534682/history
Prathmesh Kocheta,https://fantasy.premierleague.com/entry/5902896/history
Raghav L Narasimhan,https://fantasy.premierleague.com/entry/3612175/history
Samson Baretto,https://fantasy.premierleague.com/entry/29629/history
Saran Prasanth,https://fantasy.premierleague.com/entry/68554/history
Sriram Ranganath,https://fantasy.premierleague.com/entry/4659883/history
Aaryan Rathi,https://fantasy.premierleague.com/entry/6247622/history
Ankur Mokal,https://fantasy.premierleague.com/entry/5993/history
Anugreh Kumar,https://fantasy.premierleague.com/entry/45224/history
Anuj Chandna,https://fantasy.premierleague.com/entry/2954260/history
Arijit Deb,https://fantasy.premierleague.com/entry/3712849/history
Lakshmi Narayanan,https://fantasy.premierleague.com/entry/63959/history
Rahul Bhatu,https://fantasy.premierleague.com/entry/73538/history
Rohan Singh,https://fantasy.premierleague.com/entry/385369/history
Sheeraj Sengupta,https://fantasy.premierleague.com/entry/36660/history
Utsav Ojha,https://fantasy.premierleague.com/entry/29573/history
Yatin Mehra,https://fantasy.premierleague.com/entry/25972/history
Akshat Jain,https://fantasy.premierleague.com/entry/1309448/history
Amitabh Agrawal,https://fantasy.premierleague.com/entry/864413/history
Kinnari Vyas,https://fantasy.premierleague.com/entry/3915547/history
Piotr Kolodziej,https://fantasy.premierleague.com/entry/2802195/history
Prabhav VD,https://fantasy.premierleague.com/entry/157571/history
Rahul VN,https://fantasy.premierleague.com/entry/34230/history
Saswat Mishra,https://fantasy.premierleague.com/entry/15918/history
Shashwat Mehrotra,https://fantasy.premierleague.com/entry/4123513/history
Siddharth Shinde,https://fantasy.premierleague.com/entry/248794/history
Upamanyu Modukuru,https://fantasy.premierleague.com/entry/5113160/history
Vishnu Rajesh,https://fantasy.premierleague.com/entry/1443409/history
Ankur Goyal,https://fantasy.premierleague.com/entry/9555/history
Arun Goyal,https://fantasy.premierleague.com/entry/50683/history
Jay Bansal,https://fantasy.premierleague.com/entry/410700/history
Prarabdh Chaturvedi,https://fantasy.premierleague.com/entry/184328/history
Reuben Sam,https://fantasy.premierleague.com/entry/6389009/history
Shashank Jha,https://fantasy.premierleague.com/entry/3441192/history
Shiromi Chaturvedi,https://fantasy.premierleague.com/entry/26482/history
Shubham Choudhary,https://fantasy.premierleague.com/entry/14668/history
Soham Ghosh,https://fantasy.premierleague.com/entry/5913963/history
Swaroop Sarkar,https://fantasy.premierleague.com/entry/3884566/history
Vignesh Rajan,https://fantasy.premierleague.com/entry/5889697/history
Ajinkya Kale,https://fantasy.premierleague.com/entry/19906/history
Avtansh Behal,https://fantasy.premierleague.com/entry/13171/history
Ayanjit Chattopadhyay,https://fantasy.premierleague.com/entry/97348/history
Kunal Soni,https://fantasy.premierleague.com/entry/134351/history
Mohit Pant,https://fantasy.premierleague.com/entry/332497/history
Priyan Gada,https://fantasy.premierleague.com/entry/180199/history
Rajan Valecha,https://fantasy.premierleague.com/entry/6396565/history
Sanjay Krishna,https://fantasy.premierleague.com/entry/6786008/history
Snehasis Panda,https://fantasy.premierleague.com/entry/3832661/history
Sukhmani Singh,https://fantasy.premierleague.com/entry/143451/history
Vishwa Jatania,https://fantasy.premierleague.com/entry/5198677/history
Aniket Neogi,https://fantasy.premierleague.com/entry/1835336/history
Aritra Mitra,https://fantasy.premierleague.com/entry/34456/history
Ashwin Menon,https://fantasy.premierleague.com/entry/108039/history
Kunal Bhatia,https://fantasy.premierleague.com/entry/10177/history
Manan Vyas,https://fantasy.premierleague.com/entry/22671/history
Mihir Vahi,https://fantasy.premierleague.com/entry/33983/history
Pranav Mhatre,https://fantasy.premierleague.com/entry/13342/history
Rahi Reza,https://fantasy.premierleague.com/entry/113610/history
Ritobrata Nath,https://fantasy.premierleague.com/entry/13127/history
Rohan Parekh,https://fantasy.premierleague.com/entry/13754/history
Saksham Agarwal,https://fantasy.premierleague.com/entry/14035/history
Advait Keswani,https://fantasy.premierleague.com/entry/1382717/history
Angad Singh,https://fantasy.premierleague.com/entry/34863/history
Bhavika Anand,https://fantasy.premierleague.com/entry/1889364/history
Divij Ohri,https://fantasy.premierleague.com/entry/1172781/history
Harsh Rathod,https://fantasy.premierleague.com/entry/2371022/history
Jimmit Mehta,https://fantasy.premierleague.com/entry/150649/history
Rujan Borges,https://fantasy.premierleague.com/entry/5283997/history
Sachin Omprakash,https://fantasy.premierleague.com/entry/2167102/history
Samarth Makhija,https://fantasy.premierleague.com/entry/1512777/history
Sreeradh RP,https://fantasy.premierleague.com/entry/2175698/history
Sriram Srinivasan,https://fantasy.premierleague.com/entry/1223841/history
Aksh Kapoor,https://fantasy.premierleague.com/entry/81366/history
Gilson Rafael,https://fantasy.premierleague.com/entry/2377950/history
Hisham Ashraf,https://fantasy.premierleague.com/entry/22393/history
Karan Manik,https://fantasy.premierleague.com/entry/36144/history
Kashyap Reddy,https://fantasy.premierleague.com/entry/28384/history
Kevin Sequeira,https://fantasy.premierleague.com/entry/14974/history
Santosh Krishna,https://fantasy.premierleague.com/entry/14765/history
Shekhar Perugu,https://fantasy.premierleague.com/entry/5558797/history
Sreekanth Reddy,https://fantasy.premierleague.com/entry/331108/history
Vysakh Murali,https://fantasy.premierleague.com/entry/877548/history
Yasser Rajwani,https://fantasy.premierleague.com/entry/3589830/history
Divyansh Joshi,https://fantasy.premierleague.com/entry/
Jaskaran Singh,https://fantasy.premierleague.com/entry/
"""

CSV_FORM = """Team,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38
Arsenal,D,W,L,D,W,L,L,L,D,L,L,W,W,W,W,W,D,W,D,L,,,,,,,,,,,,,,,,,,
Aston Villa,D,L,W,L,W,W,W,D,W,D,W,L,D,L,L,W,W,L,D,W,,,,,,,,,,,,,,,,,,
Bournemouth,L,L,L,W,L,W,W,W,L,L,L,W,W,L,W,D,W,L,L,W,,,,,,,,,,,,,,,,,,
Brentford,L,W,L,W,D,W,L,L,W,L,W,L,L,L,D,D,W,W,L,W,,,,,,,,,,,,,,,,,,
Brighton,W,L,L,L,D,W,W,W,D,L,L,W,W,W,W,L,D,L,W,W,,,,,,,,,,,,,,,,,,
Burnley,W,L,W,W,W,W,L,W,L,W,L,W,W,W,L,W,L,L,W,L,,,,,,,,,,,,,,,,,,
Chelsea,W,L,W,L,L,L,L,D,W,L,W,L,L,D,L,W,W,W,W,W,,,,,,,,,,,,,,,,,,
Crystal Palace,L,W,L,L,L,L,L,L,D,W,W,D,D,L,W,W,W,W,L,W,,,,,,,,,,,,,,,,,,
Everton,L,W,L,W,W,W,W,L,W,L,W,W,W,W,L,L,D,W,L,L,,,,,,,,,,,,,,,,,,
Fulham,L,W,L,W,D,L,L,W,W,D,L,W,L,W,L,L,W,L,W,W,,,,,,,,,,,,,,,,,,
Leeds,W,L,L,L,L,L,W,L,L,W,W,W,D,D,L,D,L,L,L,W,,,,,,,,,,,,,,,,,,
Liverpool,W,D,W,L,L,W,W,W,L,D,L,W,W,W,W,W,L,W,W,L,,,,,,,,,,,,,,,,,,
Man City,W,W,W,L,L,L,W,W,L,W,W,L,D,L,W,L,W,W,L,L,,,,,,,,,,,,,,,,,,
Man United,D,L,L,W,W,L,W,L,D,L,L,L,D,W,D,D,L,L,W,L,,,,,,,,,,,,,,,,,,
Newcastle,D,D,W,W,W,W,L,L,L,L,L,W,L,W,W,W,L,W,L,L,,,,,,,,,,,,,,,,,,
Nottingham Forest,W,L,L,D,L,L,W,D,W,W,L,L,L,L,W,L,L,L,W,L,,,,,,,,,,,,,,,,,,
Sunderland,L,W,W,W,L,W,L,W,L,W,W,L,L,L,L,L,D,W,W,W,,,,,,,,,,,,,,,,,,
Tottenham,L,L,W,W,D,W,L,D,L,W,W,L,W,L,D,W,W,L,W,L,,,,,,,,,,,,,,,,,,
West Ham,W,W,W,L,W,L,W,W,W,W,W,L,L,L,L,L,L,W,L,L,,,,,,,,,,,,,,,,,,
Wolverhampton,L,W,W,L,W,L,L,L,W,D,L,D,D,W,D,L,L,L,L,W,,,,,,,,,,,,,,,,,,
"""

CSV_FIXTURES = """Team,GW1,GW2,GW3,GW4,GW5,GW6,GW7,GW8,GW9,GW10,GW11,GW12,GW13,GW14,GW15,GW16,GW17,GW18,GW19,GW20,GW21,GW22,GW23,GW24,GW25,GW26,GW27,GW28,GW29,GW30,GW31,GW32,GW33,GW34,GW35,GW36,GW37,GW38,cool,ShortName
Arsenal,mun,LEE,liv,NFO,MCI,new,WHU,ful,CRY,bur,sun,TOT,che,BRE,avl,WOL,eve,BHA,AVL,bou,LIV,nfo,MUN,lee,SUN,bre,tot,CHE,bha,EVE,wol,BOU,mci,NEW,FUL,whu,BUR,cry,COOL,ARS
Aston Villa,NEW,bre,CRY,eve,sun,FUL,BUR,tot,MCI,liv,BOU,lee,WOL,bha,ARS,whu,MUN,che,ars,NFO,cry,EVE,new,BRE,bou,BHA,LEE,wol,CHE,mun,WHU,nfo,SUN,ful,TOT,bur,LIV,mci,,AVL
Bournemouth,liv,WOL,tot,BHA,NEW,lee,FUL,cry,NFO,mci,avl,WHU,sun,EVE,CHE,mun,BUR,bre,che,ARS,TOT,bha,LIV,wol,AVL,eve,whu,SUN,BRE,bur,MUN,ars,new,LEE,CRY,ful,MCI,nfo,,BOU
Brentford,nfo,AVL,sun,CHE,ful,MUN,MCI,whu,LIV,cry,NEW,bha,BUR,ars,tot,LEE,wol,BOU,TOT,eve,SUN,che,NFO,avl,new,ARS,BHA,bur,bou,WOL,lee,EVE,FUL,mun,WHU,mci,CRY,liv,,BRE
Brighton,FUL,eve,MCI,bou,TOT,che,wol,NEW,mun,LEE,cry,BRE,nfo,AVL,WHU,liv,SUN,ars,whu,BUR,mci,BOU,ful,EVE,CRY,avl,bre,NFO,ARS,sun,LIV,bur,tot,CHE,new,WOL,lee,MUN,,BHA
Burnley,tot,SUN,mun,LIV,NFO,mci,avl,LEE,wol,ARS,whu,CHE,bre,CRY,new,FUL,bou,EVE,NEW,bha,MUN,liv,TOT,sun,WHU,cry,che,BRE,eve,BOU,ful,BHA,nfo,MCI,lee,AVL,ars,WOL,,BUR
Chelsea,CRY,whu,FUL,bre,mun,BHA,LIV,nfo,SUN,tot,WOL,bur,ARS,lee,bou,EVE,new,AVL,BOU,mci,ful,BRE,cry,WHU,wol,LEE,BUR,ars,avl,NEW,eve,MCI,MUN,bha,NFO,liv,TOT,sun,,CHE
Crystal Palace,che,NFO,avl,SUN,whu,LIV,eve,BOU,ars,BRE,BHA,wol,MUN,bur,ful,MCI,lee,TOT,FUL,new,AVL,sun,CHE,nfo,bha,BUR,WOL,mun,tot,LEE,mci,NEW,WHU,liv,bou,EVE,bre,ARS,,CRY
Everton,lee,BHA,wol,AVL,liv,WHU,CRY,mci,TOT,sun,FUL,mun,NEW,bou,NFO,che,ARS,bur,nfo,BRE,WOL,avl,LEE,bha,ful,BOU,MUN,new,BUR,ars,CHE,bre,LIV,whu,MCI,cry,SUN,tot,,EVE
Fulham,bha,MUN,che,LEE,BRE,avl,bou,ARS,new,WOL,eve,SUN,tot,MCI,CRY,bur,NFO,whu,cry,LIV,CHE,lee,BHA,mun,EVE,mci,sun,TOT,WHU,nfo,BUR,liv,bre,AVL,ars,BOU,wol,NEW,,FUL
Leeds,EVE,ars,NEW,ful,wol,BOU,TOT,bur,WHU,bha,nfo,AVL,mci,CHE,LIV,bre,CRY,sun,liv,MUN,new,FUL,eve,ARS,NFO,che,avl,MCI,SUN,cry,BRE,mun,WOL,bou,BUR,tot,BHA,whu,,LEE
Liverpool,BOU,new,ARS,bur,EVE,cry,che,MUN,bre,AVL,mci,NFO,whu,SUN,lee,BHA,tot,WOL,LEE,ful,ars,BUR,bou,NEW,MCI,sun,nfo,WHU,wol,TOT,bha,FUL,eve,CRY,mun,CHE,avl,BRE,,LIV
Man City,wol,TOT,bha,MUN,ars,BUR,bre,EVE,avl,BOU,LIV,new,LEE,ful,SUN,cry,WHU,nfo,sun,CHE,BHA,mun,WOL,tot,liv,FUL,NEW,lee,NFO,whu,CRY,che,ARS,bur,eve,BRE,bou,AVL,,MCI
Man United,ARS,ful,BUR,mci,CHE,bre,SUN,liv,BHA,nfo,tot,EVE,cry,WHU,wol,BOU,avl,NEW,WOL,lee,bur,MCI,ars,FUL,TOT,whu,eve,CRY,new,AVL,bou,LEE,che,BRE,LIV,sun,NFO,bha,,MUN
Newcastle,avl,LIV,lee,WOL,bou,ARS,NFO,bha,FUL,whu,bre,MCI,eve,TOT,BUR,sun,CHE,mun,bur,CRY,LEE,wol,AVL,liv,BRE,tot,mci,EVE,MUN,che,SUN,cry,BOU,ars,BHA,nfo,WHU,ful,,NEW
Nottingham Forest,BRE,cry,WHU,ars,bur,SUN,new,CHE,bou,MUN,LEE,liv,BHA,wol,eve,TOT,ful,MCI,EVE,avl,whu,ARS,bre,CRY,lee,WOL,LIV,bha,mci,FUL,tot,AVL,BUR,sun,che,NEW,mun,BOU,,NFO
Sunderland,WHU,bur,BRE,cry,AVL,nfo,mun,WOL,che,EVE,ARS,ful,BOU,liv,mci,NEW,bha,LEE,MCI,tot,bre,CRY,whu,BUR,ars,LIV,FUL,bou,lee,BHA,new,TOT,avl,NFO,wol,MUN,eve,CHE,,SUN
Tottenham,BUR,mci,BOU,whu,bha,WOL,lee,AVL,eve,CHE,MUN,ars,FUL,new,BRE,nfo,LIV,cry,bre,SUN,bou,WHU,bur,MCI,mun,NEW,ARS,ful,CRY,liv,NFO,sun,BHA,wol,avl,LEE,che,EVE,,TOT
West Ham,sun,CHE,nfo,TOT,CRY,eve,ars,BRE,lee,NEW,BUR,bou,LIV,mun,bha,AVL,mci,FUL,BHA,wol,NFO,tot,SUN,che,bur,MUN,BOU,liv,ful,MCI,avl,WOL,cry,EVE,bre,ARS,new,LEE,,WHU
Wolverhampton,MCI,bou,EVE,new,LEE,tot,BHA,sun,BUR,ful,che,CRY,avl,NFO,MUN,ars,BRE,liv,mun,WHU,eve,NEW,mci,BOU,CHE,nfo,cry,AVL,LIV,bre,ARS,whu,lee,TOT,SUN,bha,FUL,bur,,WOL
"""

CSV_CHIPS = """Team,Chip,Status,GW
Burnley QFC,Travelling Support,Valid,GW01
Liverpool QFC,Travelling Support,Valid,GW06
Fulham QFC,Fox in the Box,Valid,GW06
Burnley QFC,Bought the Ref,Valid,GW06
Liverpool QFC,Man Mark,Valid,GW07
Burnley QFC,Red Hot Form,Valid,GW07
Everton QFC,Red Hot Form,Valid,GW08
Wolverhampton QFC,Man Mark,Valid,GW09
Crystal Palace QFC,Bought the Ref,Valid,GW09
Brighton QFC,Travelling Support,Valid,GW09
Tottenham QFC,Fox in the Box,Valid,GW10
Aston Villa QFC,Travelling Support,Valid,GW10
Leeds QFC,Park the Bus,Valid,GW13
Fulham QFC,Travelling Support,Valid,GW13
West Ham QFC,Fox in the Box,Valid,GW14
Sunderland QFC,Bought the Ref,Valid,GW14
Chelsea QFC,Travelling Support,Valid,GW14
Tottenham QFC,Travelling Support,Valid,GW14
Crystal Palace QFC,Travelling Support,Valid,GW14
Burnley QFC,Park the Bus,Valid,GW14
Everton QFC,Red Hot Form,Valid,GW15
Arsenal QFC,Travelling Support,Valid,GW15
Brighton QFC,Bought the Ref,Valid,GW15
Man City QFC,Park the Bus,Valid,GW15
Man City QFC,Bought the Ref,Duplicate,GW15
Brentford QFC,Travelling Support,Returned,GW15
Leeds QFC,Bought the Ref,Valid,GW16
Brentford QFC,Bought the Ref,Valid,GW16
Brighton QFC,Red Hot Form,Valid,GW16
Liverpool QFC,Red Hot Form,Valid,GW16
Arsenal QFC,Red Hot Form,Valid,GW17
Brentford QFC,Travelling Support,Valid,GW17
Man United QFC,Bought the Ref,Valid,GW17
Nottingham QFC,Fox in the Box,Valid,GW18
Bournemouth QFC,Travelling Support,Valid,GW18
Everton QFC,Bought the Ref,Valid,GW18
Sunderland QFC,Stay Humble,Valid,GW19
Aston Villa QFC,Bought the Ref,Valid,GW19
Crystal Palace QFC,Red Hot Form,Valid,GW19
Tottenham QFC,Bought the Ref,Valid,GW19
Wolverhampton QFC,Travelling Support,Valid,GW19
Burnley QFC,Stay Humble,Valid,GW19
"""

# --- NAVIGATION ---
if 'page' not in st.session_state:
    st.session_state.page = 'home'

def go_home(): st.session_state.page = 'home'
def go_diff(): st.session_state.page = 'diff'
def go_help(): st.session_state.page = 'help'
def go_chip(): st.session_state.page = 'chip'

# --- DATA LOADERS ---
@st.cache_data
def load_data():
    try:
        df_l = pd.read_csv(io.StringIO(CSV_LINEUPS))
        df_l = df_l.iloc[:, [0, 1, 3, 4, 5, 6, 7, 8, 9]]
        df_l.columns = ['Team', 'Player', '1', '2', '3', '4', '5', '6', '7']
        
        df_r = pd.read_csv(io.StringIO(CSV_REGISTRATIONS))
        df_r['FPL_ID'] = df_r['Profile'].apply(lambda x: int(re.search(r'entry/(\d+)', str(x)).group(1)) if re.search(r'entry/(\d+)', str(x)) else None)
        
        return pd.merge(df_l, df_r[['Player', 'FPL_ID']], on='Player', how='left')
    except: return pd.DataFrame()

@st.cache_data
def load_chip_data():
    df_f = pd.read_csv(io.StringIO(CSV_FORM))
    df_x = pd.read_csv(io.StringIO(CSV_FIXTURES))
    df_c = pd.read_csv(io.StringIO(CSV_CHIPS))
    return df_f, df_x, df_c

# FPL API
@st.cache_data
def get_fpl_elements():
    try:
        r = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/", timeout=3)
        data = r.json()
        elements = {p['id']: {'name': p['web_name'], 'team_id': p['team']} for p in data['elements']}
        teams = {t['id']: t['short_name'] for t in data['teams']}
        return elements, teams
    except: return {}, {}

def get_current_gw():
    try:
        r = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/", timeout=3)
        if r.status_code == 200:
            events = r.json()['events']
            for e in events:
                if e['is_current']: return e['id']
            for e in events:
                if e['is_next']: return max(1, e['id'] - 1)
            return 38
    except: pass
    return 20

def get_picks(fpl_id, gw):
    if not fpl_id: return []
    try:
        r = requests.get(f"https://fantasy.premierleague.com/api/entry/{int(fpl_id)}/event/{gw}/picks/", timeout=3)
        return [p['element'] for p in r.json()['picks']] if r.status_code == 200 else []
    except: return []

def get_phase(gw):
    if 1 <= gw <= 5: return '1'
    if 6 <= gw <= 10: return '2'
    if 12 <= gw <= 16: return '3'
    if 17 <= gw <= 21: return '4'
    if 23 <= gw <= 27: return '5'
    if 28 <= gw <= 32: return '6'
    if 34 <= gw <= 38: return '7'
    return None

def get_opponent(team_code, gw, df_fix):
    row = df_fix[df_fix['ShortName'] == team_code]
    if row.empty: return None
    opp_code_raw = str(row[f'GW{gw}'].values[0])
    return opp_code_raw.upper()

df = load_data()
df_form, df_fix, df_used_chips = load_chip_data()
fpl_elements, fpl_teams = get_fpl_elements()
teams_list = sorted(df['Team'].unique().tolist())

# ==========================================
# PAGE: HOME
# ==========================================
if st.session_state.page == 'home':
    st.title("🏆 QFPL Hub")
    st.markdown("### Your companion for the Quatret Fantasy Premier League")
    st.divider()
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("📊 **Differentials**")
        st.write("Compare squads live.")
        st.button("Open Calculator", on_click=go_diff, use_container_width=True)
    with c2:
        st.info("📋 **Lineup Helper**")
        st.write("Check streaks & caps.")
        st.button("Open Lineup Tool", on_click=go_help, use_container_width=True)
    with c3:
        st.info("🍟 **Chip Helper**")
        st.write("Check available chips.")
        st.button("Open Chip Tool", on_click=go_chip, use_container_width=True)

# ==========================================
# PAGE: DIFFERENTIALS
# ==========================================
elif st.session_state.page == 'diff':
    st.button("🏠 Home", on_click=go_home)
    st.header("📊 Differential Calculator")
    
    c1, c2 = st.columns(2)
    with c1: t_a = st.selectbox("Your Team", teams_list)
    with c2: gw = st.number_input("Gameweek", 1, 38, 21)

    if st.button("Calculate", type="primary"):
        phase = get_phase(gw)
        if not phase:
            st.error(f"Gameweek {gw} is not part of a standard QFPL Phase (Cup/Break week).")
        else:
            t_b = get_opponent(t_a, gw, df_fix)
            if not t_b:
                st.error("Could not determine opponent.")
            else:
                real_gw = get_current_gw()
                fetch_gw = min(gw, real_gw)
                
                info_msg = f"**Matchup:** {t_a} vs {t_b} (Phase {phase})"
                if gw > real_gw:
                    info_msg += f" - *Using available squads from GW{fetch_gw}*"
                st.info(info_msg)

                if phase not in df.columns or df[phase].isnull().all():
                    st.error(f"Lineup data for Phase {phase} is unavailable. Please check back later.")
                else:
                    prog = st.progress(0, "Fetching...")
                    
                    def get_h(tm, s, e):
                        h = {}
                        mask = (df['Team'] == tm) & (df[phase].astype(str).str.upper().isin(['S', 'C']))
                        ros = df[mask]
                        tot = len(ros)
                        for i, (_, r) in enumerate(ros.iterrows()):
                            prog.progress(int(s + ((i+1)/tot * (e-s))), f"Loading {tm}...")
                            mul = 2 if str(r[phase]).upper() == 'C' else 1
                            for p in get_picks(r['FPL_ID'], fetch_gw): h[p] = h.get(p, 0) + mul
                        return h

                    ha = get_h(t_a, 0, 50)
                    hb = get_h(t_b, 50, 100)
                    prog.empty()

                    res = []
                    for pid in set(ha) | set(hb):
                        net = ha.get(pid, 0) - hb.get(pid, 0)
                        if net != 0:
                            p = fpl_elements.get(pid, {'name': 'Unknown', 'team_id': 0})
                            res.append({'Player': p['name'], 'Team': fpl_teams.get(p['team_id'], '-'), f'{t_a}': ha.get(pid, 0), f'{t_b}': hb.get(pid, 0), 'Net': net})
                    
                    if not res: st.success("Teams are perfectly matched!")
                    else:
                        rdf = pd.DataFrame(res).sort_values(by='Net', key=abs, ascending=False)
                        st.dataframe(rdf.style.map(lambda v: f'background-color: {"#d1e7dd" if v>0 else "#f8d7da" if v<0 else ""}; color: black', subset=['Net']), use_container_width=True, hide_index=True)

# ==========================================
# PAGE: LINEUP HELPER
# ==========================================
elif st.session_state.page == 'help':
    st.button("🏠 Home", on_click=go_home)
    st.header("📋 Lineup Submission Helper")
    
    c1, c2 = st.columns(2)
    with c1: my_team = st.selectbox("Team", teams_list)
    with c2: n_ph = st.selectbox("Submitting for Phase", [4, 5, 6, 7])

    data = []
    for _, r in df[df['Team'] == my_team].iterrows():
        p1, p2 = str(n_ph - 1), str(n_ph - 2)
        must = (p1 in df.columns and p2 in df.columns and str(r[p1]).upper() == 'B' and str(r[p2]).upper() == 'B')
        
        used = 0
        for i in range(1, n_ph):
            if str(i) in df.columns and str(r[str(i)]).upper() == 'C': used += 1
        
        data.append({
            "Player": r['Player'],
            "Bench Status": "⚠️ MUST START" if must else "OK",
            "Captaincy": "❌ Used" if used else "✅ Available",
            "_sort": 0 if must else 1
        })
    
    df_out = pd.DataFrame(data).sort_values(by=['_sort', 'Player'])
    
    if any(df_out['_sort'] == 0):
        st.error("🚨 You have players on a 2-game bench streak! They MUST play.")
    
    st.dataframe(
        df_out.style.apply(lambda x: ['background-color: #f8d7da; font-weight: bold'] * len(x) if x['_sort'] == 0 else ['background-color: #fff3cd'] * len(x) if x['Captaincy'] == "❌ Used" else [''] * len(x), axis=1).hide(subset=['_sort'], axis='columns'),
        use_container_width=True,
        hide_index=True
    )
    st.link_button("🚀 Submit Lineup", "https://docs.google.com/forms/d/e/1FAIpQLSfIPWcBe5LpLmI8dq5Jqxvw2ug9_9d2Ha9RIyREMEiBbNmyzQ/viewform?usp=header", type="primary")

# ==========================================
# PAGE: CHIP HELPER
# ==========================================
elif st.session_state.page == 'chip':
    st.button("🏠 Home", on_click=go_home)
    st.header("🍟 Chip Submission Helper")
    st.markdown("Check eligibility for special chips.")

    c1, c2 = st.columns(2)
    with c1: team = st.selectbox("Select Team", teams_list)
    with c2: curr_gw = st.number_input("Upcoming Gameweek", 1, 38, 21)

    chips = [
        {"name": "Red Hot Form", "desc": "Requires 4 consecutive wins.", "type": "form"},
        {"name": "Stay Humble", "desc": "Play vs opponent you previously lost to.", "type": "humble"},
        {"name": "Travelling Support", "desc": "Standard chip.", "type": "std"},
        {"name": "Fox in the Box", "desc": "Standard chip.", "type": "std"},
        {"name": "Bought the Ref", "desc": "Standard chip.", "type": "std"},
        {"name": "Man Mark", "desc": "Standard chip.", "type": "std"},
        {"name": "Park the Bus", "desc": "Standard chip.", "type": "std"}
    ]

    short_to_full = dict(zip(df_fix['ShortName'], df_fix['Team']))
    full_team_name = short_to_full.get(team, team)
    curr_phase = get_phase(curr_gw)
    
    chips_used_in_phase = 0
    if curr_phase:
        phase_ranges = {'1': (1,5), '2': (6,10), '3': (12,16), '4': (17,21), '5': (23,27), '6': (28,32), '7': (34,38)}
        start, end = phase_ranges[curr_phase]
        
        phase_usage = df_used_chips[
            (df_used_chips['Team'].str.contains(team, case=False)) & 
            (df_used_chips['Status'] == 'Valid') & 
            (df_used_chips['Chip'] != 'Red Hot Form')
        ].copy()
        
        # Use raw string r'' for regex pattern
        phase_usage['GW_Int'] = phase_usage['GW'].str.extract(r'(\d+)').astype(int)
        chips_used_in_phase = phase_usage[(phase_usage['GW_Int'] >= start) & (phase_usage['GW_Int'] <= end)].shape[0]

    phase_limit_reached = (chips_used_in_phase >= 2)
    
    results = []
    
    def is_used_season(c_name):
        matches = df_used_chips[
            (df_used_chips['Team'].str.contains(team, case=False)) & 
            (df_used_chips['Chip'] == c_name) & 
            (df_used_chips['Status'] == 'Valid')
        ]
        return not matches.empty

    for c in chips:
        if c['name'] != "Red Hot Form" and is_used_season(c['name']):
            results.append({"Chip": c['name'], "Status": "Played", "Reason": "Already used this season", "_color": "grey"})
            continue
        
        if c['name'] != "Red Hot Form" and phase_limit_reached:
            results.append({"Chip": c['name'], "Status": "Unavailable", "Reason": f"Phase Limit Reached ({chips_used_in_phase}/2 chips used)", "_color": "red"})
            continue

        status, reason, color = "Available", "Ready", "green"
        
        if c['type'] == "form":
            row = df_form[df_form['Team'] == full_team_name]
            if not row.empty:
                form_seq = []
                for g in range(curr_gw - 4, curr_gw):
                    if g > 0: form_seq.append(str(row[str(g)].values[0]).upper())
                
                if form_seq != ['W', 'W', 'W', 'W']:
                    status, reason, color = "Unavailable", f"Form is {form_seq} (Need 4 Wins)", "red"
        
        elif c['type'] == "humble":
            fix_row = df_fix[df_fix['ShortName'] == team]
            if not fix_row.empty:
                opp_code = str(fix_row[f'GW{curr_gw}'].values[0]).upper()
                prev_gw = None
                for g in range(1, curr_gw):
                    if str(fix_row[f'GW{g}'].values[0]).upper() == opp_code:
                        prev_gw = g
                        break
                
                if not prev_gw:
                    status, reason, color = "Unavailable", f"No previous game vs {opp_code}", "red"
                else:
                    form_row = df_form[df_form['Team'] == full_team_name]
                    res = str(form_row[str(prev_gw)].values[0]).upper()
                    if res != 'L':
                        status, reason, color = "Unavailable", f"Result vs {opp_code} was {res} (Need Loss)", "red"
                    else:
                        reason = f"Lost to {opp_code} in GW{prev_gw}"

        results.append({"Chip": c['name'], "Status": status, "Reason": reason, "_color": color})

    df_chips_disp = pd.DataFrame(results)
    
    def style_chips(row):
        c = row['_color']
        if c == 'green': return ['background-color: #d1e7dd; color: black'] * len(row)
        if c == 'red': return ['background-color: #f8d7da; color: black'] * len(row)
        return ['background-color: #e2e3e5; color: gray'] * len(row)

    st.dataframe(
        df_chips_disp.style.apply(style_chips, axis=1).hide(subset=['_color'], axis='columns'),
        use_container_width=True,
        hide_index=True
    )

    st.divider()
    st.link_button("🍟 Play a Chip", "https://docs.google.com/forms/d/e/1FAIpQLSeCOyvw4b7Ka2S19oBrhJd9SBnfCZM0Ycap-9Q8ng50hvKgcQ/viewform?usp=header", type="primary")
