import re
import socket
from dns import resolver

class dns_resolve_hostname():

    def dns_determiner(request_item):
                
        regex = re.compile("(\d{1,3}\.){3}\d{1,3}")
        request_item = request_item.lower().strip()

        if regex.match(request_item):
            return ("IP") # IP address

        else:
            return ("A") # A-record

    def dns_reporter(request_item, dns_type):
        dns_query = resolver.Resolver()
        dns_query.nameservers = ['172.31.1.1']
        
        answer_list = []

        request_item = request_item.lower().strip()
        
        # If request_item is IP record
        if dns_type == "IP":
            try:
                answer = socket.gethostbyaddr(request_item)[0]
                return answer

            except:
                answer = ''
                return answer
        
        # If request_item is A record

        elif dns_type == "A":
            try:
                question = dns_query.resolve(request_item, search=True) #Auto append DNS suffixes
                
                for answer in question:
                    dns_answer = answer.to_text()
                    answer_list.append(dns_answer)
                
                return answer_list

            except:
                answer_list == ''
                return answer_list

    def __init__(self, hostname):
        
        dns_type = dns_resolve_hostname.dns_determiner(hostname)

        dns_answer = dns_resolve_hostname.dns_reporter(hostname, dns_type)
                    
        if len(dns_answer) == 1:
            if dns_type == 'A':
                self.ip_addr = dns_answer[0]
                self.dns_hostname = hostname
            
            elif dns_type == 'IP':
                self.ip_addr = hostname
                self.dns_hostname = dns_answer[0]
        
        else:
            if dns_type == 'A':
                self.ip_addr = dns_answer
                self.dns_hostname = hostname
            
            elif dns_type == 'IP':
                self.ip_addr = hostname
                self.dns_hostname = dns_answer               