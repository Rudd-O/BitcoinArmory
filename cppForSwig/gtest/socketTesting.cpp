#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <fcntl.h>
#include <iostream>
#include <errno.h>
#include <string.h>
#include <string>

using namespace std;

int main(void)
{
   int sockfd = socket(AF_INET, SOCK_STREAM, 0);

   if(sockfd < 0)
   {
       cout << "failed to create socket with errno: " << errno << endl;
       return 0;
   }

   int flags = fcntl(sockfd, F_GETFL, 0);
   if(flags < 0)
   {
      cout << "failed to get socket flags with errno: " << errno << endl;
      return 0;
   }

   flags &= ~O_NONBLOCK;
   if(fcntl(sockfd, F_SETFL, 0))
   {
      cout << "failed to set socket flags with errno: " << errno << endl;
      return 0;
   }

   /*struct flock lock;
   lock.l_type = F_WRLCK;
   lock.l_start = 0;
   lock.l_whence = SEEK_SET;
   lock.l_len = 0;   

   if(fcntl(sockfd, F_SETLKW, &lock) != 0)
   {
      cout << "failed to lock socket with errno: " << errno << endl;
      return 0;
   }*/

   string host("127.0.0.1");
   unsigned long tcp_ia = inet_addr(host.c_str());

   struct sockaddr_in sa;
   memset(&sa, 0, sizeof(sa));

   sa.sin_family = AF_INET;
   sa.sin_port   = htons(9999);
   sa.sin_addr.s_addr = tcp_ia;

   if(bind(sockfd, (struct sockaddr*)&sa, sizeof(sa)) < 0)
   {
      cout << "failed to bind socket with errno: " << errno << endl;
      return 0;
   }
   
   if(listen(sockfd, 10) < 0)
   {
      cout << "failed to listen on socket with errno: " << errno << endl;	
      return 0;
   }

   struct sockaddr_in accept_sa;
   socklen_t socklen = sizeof(accept_sa);

   if(accept(sockfd, (struct sockaddr*)&accept_sa, &socklen) < 0)
   {
      cout << "failed to accept on socket with errno: " << errno << endl;
      return 0;
   }

   cout << "success" << endl;
   close(sockfd);

   return 0;
}
