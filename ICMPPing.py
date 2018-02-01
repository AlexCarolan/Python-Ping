import socket
import os
import sys
import struct
import time
import select
import binascii  


ICMP_ECHO_REQUEST = 8 #ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0 #ICMP type code for echo reply messages

ARRIVED = 0
TOTAL = 0
LOST = 0
MIN = 0
MAX = 0

def checksum(string): 
	csum = 0
	countTo = (len(string) // 2) * 2  
	count = 0

	while count < countTo:
		thisVal = ord(string[count+1]) * 256 + ord(string[count]) 
		csum = csum + thisVal 
		csum = csum & 0xffffffff  
		count = count + 2
	
	if countTo < len(string):
		csum = csum + ord(string[len(string) - 1])
		csum = csum & 0xffffffff 
	
	csum = (csum >> 16) + (csum & 0xffff)
	csum = csum + (csum >> 16)
	answer = ~csum 
	answer = answer & 0xffff 
	answer = answer >> 8 | (answer << 8 & 0xff00)
	
	if sys.platform == 'darwin':
		answer = socket.htons(answer) & 0xffff		
	else:
		answer = socket.htons(answer)

	return answer 
	
def receiveOnePing(icmpSocket, destinationAddress, ID, timeout, timeSent):
	
	global ARRIVED
	global TOTAL
	global LOST
	global MIN
	global MAX
	
	# 1. Wait for the socket to receive a reply
	# 2. Once received, record time of receipt, otherwise, handle a timeout
	try:
		packet = icmpSocket.recv(1024)
		recived = time.time()
	except:
		print("Time Out")
		LOST = LOST + 1
		return
	
	ARRIVED = ARRIVED + 1
	
	# 3. Compare the time of receipt to time of sending, producing the total network delay
	delay = recived - timeSent
	delay = round(delay * 1000.0, 3)
	
	# Record minimum delay
	if MIN == 0 or delay < MIN:
		MIN = delay
		
	# Record Maximum delay
	if delay > MAX :
		MAX = delay
	
	TOTAL = TOTAL + delay
	# 4. Unpack the packet header for useful information, including the ID
	# 5. Check that the ID matches between the request and reply
	# 6. Return total network delay
	print(str(delay) +" ms")
	
def sendOnePing(icmpSocket, destinationAddress, ID):
	# 1. Build ICMP header
	header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, ICMP_ECHO_REPLY, 0, ID, 1)
	# 2. Checksum ICMP packet using given function
	chkSum = checksum(header)
	# 3. Insert checksum into packet
	packet = struct.pack("bbHHh", ICMP_ECHO_REQUEST, ICMP_ECHO_REPLY, chkSum, ID, 1)
	# 4. Send packet using socket
	icmpSocket.send(packet)
	# 5. Record time of sending
	timeSent = time.time()
	return timeSent
	

def doOnePing(destinationAddress, timeout, ID): 
	# 1. Create ICMP socket
	icmp = socket.getprotobyname("icmp")
	sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
	sock.connect((destinationAddress, 80))
	sock.settimeout(timeout)
	# 2. Call sendOnePing function
	timeSent = sendOnePing(sock, destinationAddress, ID)
	# 3. Call receiveOnePing function
	receiveOnePing(sock, destinationAddress, ID, timeout, timeSent)
	# 4. Close ICMP socket
	sock.close()
	# 5. Return total network delay
	
def ping(host):
	sampleSize = int(input("Input the number packets to send: "))
	timeout = int(input("Input the timeout value in seconds: "))
	# 1. Look up hostname, resolving it to an IP address
	ipAddress = socket.gethostbyname(host)
	# 2. Call doOnePing function, approximately every second
	for x in range(0,sampleSize):
		doOnePing(ipAddress, timeout, x)
		time.sleep(1)
	# 3. Print out the returned delay
	# 4. Continue this process until stopped	
	
host = input("Input the adress of the site: ")
ping(host)

# Print the results
print("Packets Lost: " + str(LOST))
print("Packets Recived: " + str(ARRIVED))
print("Average Latency: " + str(round(TOTAL/ARRIVED,3)) + " ms")
print("Minimum Latency: " + str(round(MIN,3)) + " ms")
print("Maximum Latency: " + str(round(MAX,3)) + " ms")



