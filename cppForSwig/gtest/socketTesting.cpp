#include <unistd.h>
#include <sys/socket.h>
#include <fcntl.h>
#include <iostream>
#include <errno.h>

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

   struct flock lock;
   lock.l_type = F_WRLCK;
   lock.l_start = 0;
   lock.l_whence = SEEK_SET;
   lock.l_len = 0;   

   if(fcntl(sockfd, F_SETLKW, &lock) != 0)
   {
      cout << "failed to lock socket with errno: " << errno << endl;
      return 0;
   }

   cout << "success" << endl;
   close(sockfd);

   return 0;
}
