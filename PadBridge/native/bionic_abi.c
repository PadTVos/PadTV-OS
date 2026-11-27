/* Limited unversioned x86-64 ABI adapter, not a Bionic replacement.
 * Only approved scalar/pointer ABIs are accepted by native_elf.rs. Android FILE,
 * pthread structures, TLS, versioned symbols and linker namespaces are rejected.
 * Standard memory functions resolve to the already loaded glibc implementation. */
#include <errno.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
int *__errno(void){return &errno;}
int __system_property_get(const char *name,char *value){(void)name;if(value)value[0]=0;return 0;}
int __android_log_write(int priority,const char *tag,const char *text){return fprintf(stderr,"Android log %d/%s: %s\n",priority,tag?tag:"",text?text:"");}
int __android_log_print(int priority,const char *tag,const char *fmt,...){fprintf(stderr,"Android log %d/%s: ",priority,tag?tag:"");va_list args;va_start(args,fmt);int n=vfprintf(stderr,fmt,args);va_end(args);fputc('\n',stderr);return n;}
void __assert2(const char *file,int line,const char *function,const char *message){fprintf(stderr,"Android assertion %s:%d %s: %s\n",file,line,function,message);abort();}
