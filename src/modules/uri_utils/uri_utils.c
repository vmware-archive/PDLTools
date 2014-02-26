/**
 * File: uri_utils.c
 * C backend for "uri_utils.sql"
*/

#include <postgres.h>
#include <fmgr.h>
#include<sys/time.h>

#ifdef PG_MODULE_MAGIC
PG_MODULE_MAGIC;
#endif

#include <funcapi.h>
#include <utils/array.h>
#include <utils/lsyscache.h>

#include <uriparser/Uri.h>
#include <string.h>

char* strenc(char* const dst,const char* const src);
char* memenc(char* const dst,const char* const src,int len);
void memcpz(char* const dst,const char* const src,int len);

char* strenc(char* const dst,const char* const src)
{
  return memenc(dst,src,strlen(src));
/*
  char* dst_ptr=dst;
  const char* src_ptr=src;
  while (*src_ptr!='\0') {
    if ((*src_ptr=='\\')||(*src_ptr=='"')) {
      *dst_ptr='\\';
      ++dst_ptr;
    }
    *dst_ptr=*src_ptr;
    ++dst_ptr;
    ++src_ptr;
  }
  *dst_ptr='\0';
  return dst_ptr;
*/
}

char* memenc(char* const dst,const char* const src,int len)
{
/*
  The following characters cause the entire string to become quoted.
  (There is no leeway regarding when to quote and when not.)

  \ ' " , { } space
*/
  bool quote=false;
  const char* src_ptr=src;
  for(int i=0;i<len;++i) {
    switch (*src_ptr) {
      case ' ':
      case '\\':
      case '"':
      case ',':
      case '{':
      case '}':
        quote=true;
    }
    ++src_ptr;
  } 
  if (len==0) {
    quote=true;
  }
  char* dst_ptr;
  if (!quote) {
    memcpy(dst,src,len);
    dst_ptr=dst+len;
    *dst_ptr='\0';
  } else {
    src_ptr=src;
    dst_ptr=dst;
    *dst_ptr='"';
    ++dst_ptr;
    for(int i=0;i<len;++i) {
      switch (*src_ptr) {
        case ' ':
        case '\\':
        case '"':
        case ',':
        case '{':
        case '}':
          *dst_ptr='\\';
          ++dst_ptr;
      }
      *dst_ptr=*src_ptr;
      ++dst_ptr;
      ++src_ptr;
    }
    *dst_ptr='"';
    ++dst_ptr;
    *dst_ptr='\0';
  }
  return dst_ptr;
}

void memcpz(char* const dst,const char* const src,int len)
{
  memcpy(dst,src,len);
  dst[len]='\0';
}

PG_FUNCTION_INFO_V1(parse_uri);

Datum parse_uri(PG_FUNCTION_ARGS);

Datum parse_uri(PG_FUNCTION_ARGS)
{
  TupleDesc tupledesc;
  AttInMetadata *attinmeta;
  text* input=PG_GETARG_TEXT_P(0);
    /* Function is defined STRICT in SQL, so no NULL check is needed. */
  bool normalize=PG_GETARG_BOOL(1);
  bool parse_query=PG_GETARG_BOOL(2);

  char* inp=palloc((1+VARSIZE(input)-VARHDRSZ)*sizeof(char));
  if (!inp) {
    ereport(ERROR,
            (errcode(ERRCODE_OUT_OF_MEMORY),
             errmsg("Memory allocation failed.")));
    PG_RETURN_NULL();
  }
  memcpy(inp,VARDATA(input),VARSIZE(input)-VARHDRSZ);
  inp[VARSIZE(input)-VARHDRSZ]='\0';

  /* Function internals start here */

  int i;
  int memctr;
  UriPathSegmentA* pathseg;
  int quit;
  char* writehere;
  UriParserStateA state;
  UriUriA uri;

  state.uri = &uri;

  if (uriParseUriA(&state, inp) != URI_SUCCESS) {
    uriFreeUriMembersA(&uri);
/*
    ereport(ERROR,
            (errcode(ERRCODE_FEATURE_NOT_SUPPORTED),
             errmsg("Unable to parse URI.")));
*/
    PG_RETURN_NULL();
  }

  if (normalize) {
    if (uriNormalizeSyntaxA(&uri) != URI_SUCCESS) {
      uriFreeUriMembersA(&uri);
      PG_RETURN_NULL();
    }
  }

  UriQueryListA* queryList=NULL;
  int itemCount;
  if (parse_query&&(uri.query.afterLast!=uri.query.first)) {
    if (uriDissectQueryMallocA(&queryList, &itemCount, uri.query.first,
                               uri.query.afterLast) != URI_SUCCESS) {
      uriFreeUriMembersA(&uri);
      uriFreeQueryListA(queryList);
      PG_RETURN_NULL();
    }
  }
    

  /* Function internals finish here */
   
  if (get_call_result_type(fcinfo, NULL, &tupledesc) != TYPEFUNC_COMPOSITE) {
    ereport(ERROR,
            (errcode(ERRCODE_FEATURE_NOT_SUPPORTED),
             errmsg("function returning record called in context "
                    "that cannot accept type record")));
    PG_RETURN_NULL();
  }
  /* This error should never happen, because the SQL function is defined
     as returning a uri_type. */

  attinmeta = TupleDescGetAttInMetadata(tupledesc);

  char** retval=(char**) palloc(13*sizeof(char*));
  if (!retval) {
    ereport(ERROR,
            (errcode(ERRCODE_OUT_OF_MEMORY),
             errmsg("Memory allocation failed.")));
    PG_RETURN_NULL();
  }
  if (uri.scheme.afterLast==uri.scheme.first) {
    retval[0]=NULL;
  } else {
    retval[0]=(char*) palloc((1+(uri.scheme.afterLast-uri.scheme.first))*sizeof(char)); /* scheme, e.g. "http" */
    if (!retval[0]) {
      ereport(ERROR,
              (errcode(ERRCODE_OUT_OF_MEMORY),
               errmsg("Memory allocation failed.")));
      PG_RETURN_NULL();
    }
    memcpz(retval[0],uri.scheme.first,uri.scheme.afterLast-uri.scheme.first);
  }
  if (uri.userInfo.afterLast==uri.userInfo.first) {
    retval[1]=NULL;
  } else {
    retval[1]=(char*) palloc((1+(uri.userInfo.afterLast-uri.userInfo.first))*sizeof(char)); /* userInfo, e.g. "gpadmin" */
    if (!retval[1]) {
      ereport(ERROR,
              (errcode(ERRCODE_OUT_OF_MEMORY),
               errmsg("Memory allocation failed.")));
      PG_RETURN_NULL();
    }
    memcpz(retval[1],uri.userInfo.first,uri.userInfo.afterLast-uri.userInfo.first);
  }
  if (uri.hostText.afterLast==uri.hostText.first) {
    retval[2]=NULL;
  } else {
    retval[2]=(char*) palloc((1+(uri.hostText.afterLast-uri.hostText.first))*sizeof(char)); /* hostText, e.g. "192.165.0.0" */
    if (!retval[2]) {
      ereport(ERROR,
              (errcode(ERRCODE_OUT_OF_MEMORY),
               errmsg("Memory allocation failed.")));
      PG_RETURN_NULL();
    }
    memcpz(retval[2],uri.hostText.first,uri.hostText.afterLast-uri.hostText.first);
  }
  if (uri.hostData.ip4==NULL) {
    retval[3]=NULL;
  } else {
    retval[3]=(char*) palloc(17*sizeof(char)); /* IPv4 */
    if (!retval[3]) {
      ereport(ERROR,
              (errcode(ERRCODE_OUT_OF_MEMORY),
               errmsg("Memory allocation failed.")));
      PG_RETURN_NULL();
    }
    memcpy(retval[3],"\\000\\000\\000\\000",17);
    for(i=0;i<4;++i) {
      retval[3][1+4*i]+=uri.hostData.ip4->data[i]>> 6;
      retval[3][2+4*i]+=(uri.hostData.ip4->data[i]>> 3)&7;
      retval[3][3+4*i]+=uri.hostData.ip4->data[i]&7;
    }
  }
  if (uri.hostData.ip6==NULL) {
    retval[4]=NULL;
  } else {
    retval[4]=(char*) palloc(65*sizeof(char)); /* IPv6 */
    if (!retval[4]) {
      ereport(ERROR,
              (errcode(ERRCODE_OUT_OF_MEMORY),
               errmsg("Memory allocation failed.")));
      PG_RETURN_NULL();
    }
    memcpy(retval[4],"\\000\\000\\000\\000\\000\\000\\000\\000\\000\\000\\000\\000\\000\\000\\000\\000",65);
    for(i=0;i<16;++i) {
      retval[4][1+4*i]+=uri.hostData.ip6->data[i]>> 6;
      retval[4][2+4*i]+=(uri.hostData.ip6->data[i]>> 3)&7;
      retval[4][3+4*i]+=uri.hostData.ip6->data[i]&7;
    }
  }
  if (uri.hostData.ipFuture.afterLast==uri.hostData.ipFuture.first) {
    retval[5]=NULL;
  } else {
    retval[5]=(char*) palloc((1+(uri.hostData.ipFuture.afterLast-uri.hostData.ipFuture.first))*sizeof(char)); /* ipFuture, text field */
    if (!retval[5]) {
      ereport(ERROR,
              (errcode(ERRCODE_OUT_OF_MEMORY),
               errmsg("Memory allocation failed.")));
      PG_RETURN_NULL();
    }
    memcpz(retval[5],uri.hostData.ipFuture.first,uri.hostData.ipFuture.afterLast-uri.hostData.ipFuture.first);
  }
  if (uri.portText.afterLast==uri.portText.first) {
    retval[6]=NULL;
  } else {
    retval[6]=(char*) palloc((1+(uri.portText.afterLast-uri.portText.first))*sizeof(char)); /* portText, e.g. "80" */
    if (!retval[6]) {
      ereport(ERROR,
              (errcode(ERRCODE_OUT_OF_MEMORY),
               errmsg("Memory allocation failed.")));
      PG_RETURN_NULL();
    }
    memcpz(retval[6],uri.portText.first,uri.portText.afterLast-uri.portText.first);
  }
  if (uri.pathHead==NULL) {
    retval[7]=NULL;
  } else {
    memctr=2;
    pathseg=uri.pathHead;
    do {
      quit=((pathseg==uri.pathTail)||(pathseg->next==NULL));
      memctr+=3+2*(pathseg->text.afterLast-pathseg->text.first);
      pathseg=pathseg->next;
    } while (!quit);
    if (memctr==2) {
      ++memctr;
    }
    retval[7]=(char*) palloc(memctr*sizeof(char)); /* path */
    /* e.g. "{usr,local,lib}" */
    if (!retval[7]) {
      ereport(ERROR,
              (errcode(ERRCODE_OUT_OF_MEMORY),
               errmsg("Memory allocation failed.")));
      PG_RETURN_NULL();
    }
    writehere=retval[7];
    *writehere='{';
    ++writehere;
    pathseg=uri.pathHead;
    do {
      quit=((pathseg==uri.pathTail)||(pathseg->next==NULL));
      writehere=memenc(writehere,pathseg->text.first,pathseg->text.afterLast-pathseg->text.first);
      *writehere=',';
      ++writehere;
      pathseg=pathseg->next;
    } while (!quit);
    if (memctr!=3) {
      --writehere;
    }
    memcpy(writehere,"}",2);
  }
  if (uri.query.afterLast==uri.query.first) {
    retval[8]=NULL;
  } else {
    retval[8]=(char*) palloc((1+(uri.query.afterLast-uri.query.first))*sizeof(char)); /* query without leading "?" */
    if (!retval[8]) {
      ereport(ERROR,
              (errcode(ERRCODE_OUT_OF_MEMORY),
               errmsg("Memory allocation failed.")));
      PG_RETURN_NULL();
    }
    memcpz(retval[8],uri.query.first,uri.query.afterLast-uri.query.first);
  }
  if (uri.fragment.afterLast==uri.fragment.first) {
    retval[9]=NULL;
  } else {
    retval[9]=(char*) palloc((1+(uri.fragment.afterLast-uri.fragment.first))*sizeof(char)); /* fragment without leading "#" */
    if (!retval[9]) {
      ereport(ERROR,
              (errcode(ERRCODE_OUT_OF_MEMORY),
               errmsg("Memory allocation failed.")));
      PG_RETURN_NULL();
    }
    memcpz(retval[9],uri.fragment.first,uri.fragment.afterLast-uri.fragment.first);
  }
  if (uri.absolutePath) {
    retval[10]=(char*) palloc(5*sizeof(char)); /* absolutePath */
    if (!retval[10]) {
      ereport(ERROR,
              (errcode(ERRCODE_OUT_OF_MEMORY),
               errmsg("Memory allocation failed.")));
      PG_RETURN_NULL();
    }
    memcpy(retval[10],"true",5);
  } else {
    retval[10]=(char*) palloc(6*sizeof(char)); /* absolutePath */
    if (!retval[10]) {
      ereport(ERROR,
              (errcode(ERRCODE_OUT_OF_MEMORY),
               errmsg("Memory allocation failed.")));
      PG_RETURN_NULL();
    }
    memcpy(retval[10],"false",6);
  }

  if (parse_query) {
    int key_counter=2;
    int val_counter=2;
    int counter=0;
    for(UriQueryListA* it=queryList;(counter!=itemCount)&&(it!=NULL);
        it=it->next,++counter) {
      if (it->key==NULL) {
        key_counter+=3; /* should never reach here. */
      } else {
        key_counter+=3+2*strlen(it->key);
      }
      if (it->value==NULL) {
        val_counter+=3; /* currently no way to distinguish empty string
                           value (?a=) from null value (?a). This is a GPDB
                           limitation. */
      } else {
        val_counter+=3+2*strlen(it->value);
      }
    }
    if (key_counter==2) {
      ++key_counter;
    }
    if (val_counter==2) {
      ++val_counter;
    }
    retval[11]=palloc(key_counter*sizeof(char));
    if (!retval[11]) {
      ereport(ERROR,
              (errcode(ERRCODE_OUT_OF_MEMORY),
               errmsg("Memory allocation failed.")));
      PG_RETURN_NULL();
    }
    retval[12]=palloc(val_counter*sizeof(char));
    if (!retval[12]) {
      ereport(ERROR,
              (errcode(ERRCODE_OUT_OF_MEMORY),
               errmsg("Memory allocation failed.")));
      PG_RETURN_NULL();
    }
    retval[11][0]='{';
    retval[12][0]='{';
    char* key_ptr=retval[11]+1;
    char* val_ptr=retval[12]+1;
    counter=0;
    for(UriQueryListA* it=queryList;(counter!=itemCount)&&(it!=NULL);
        it=it->next,++counter) {
      if (it->key==NULL) {
        *key_ptr='"';
        ++key_ptr;
        *key_ptr='"';
        ++key_ptr;
        *key_ptr=',';
        ++key_ptr;
        /* should never reach here. */
      } else {
        key_ptr=strenc(key_ptr,it->key);
        *key_ptr=',';
        ++key_ptr;
      }
      if (it->value==NULL) {
        *val_ptr='"';
        ++val_ptr;
        *val_ptr='"';
        ++val_ptr;
        *val_ptr=',';
        ++val_ptr;
                        /* currently no way to distinguish empty string
                           value (?a=) from null value (?a). This is a GPDB
                           limitation. */
      } else {
        val_ptr=strenc(val_ptr,it->value);
        *val_ptr=',';
        ++val_ptr;
      }
    }
    if (key_counter!=3) {
      --key_ptr;
    }
    memcpy(key_ptr,"}",2);
    if (val_counter!=3) {
      --val_ptr;
    }
    memcpy(val_ptr,"}",2);
    uriFreeQueryListA(queryList);
  } else {
    retval[11]=NULL;
    retval[12]=NULL;
  }

  /* There is no need to call pfree. It's called automatically. */

  HeapTuple tuple;
  Datum result;

  tuple=BuildTupleFromCStrings(attinmeta,retval);
  result=HeapTupleGetDatum(tuple);

  /* Free memory start */
  uriFreeUriMembersA(&uri);
  /* Free memory finish */

  PG_RETURN_DATUM(result);
}

/*
Legal characters in a URI:

A-Za-z0-9-._~:/?#[]@!$&'()*+,;=

as well as %, when appearing in the context %[A-Fa-f0-9][A-Fa-f0-9]

A colon (:) must be present.

The legal characters correspond to the following ASCII ranges:

33,35-44,46-59,61,63-91,93,95,97-122,126

The character ':' is ASCII 58
*/

typedef struct UriListStruct {
  UriUriA uri;
  char* uri_text;
  struct UriListStruct* next;
} UriList;

PG_FUNCTION_INFO_V1(extract_uri);

Datum extract_uri(PG_FUNCTION_ARGS);

Datum extract_uri(PG_FUNCTION_ARGS)
{
  TupleDesc tupledesc;
  AttInMetadata *attinmeta;
  text* input=PG_GETARG_TEXT_P(0);
    /* Function is defined STRICT in SQL, so no NULL check is needed. */
  bool normalize=PG_GETARG_BOOL(1);

  char* inp=palloc((1+VARSIZE(input)-VARHDRSZ)*sizeof(char));
  if (!inp) {
    ereport(ERROR,
            (errcode(ERRCODE_OUT_OF_MEMORY),
             errmsg("Memory allocation failed.")));
    PG_RETURN_NULL();
  }
  memcpz(inp,VARDATA(input),VARSIZE(input)-VARHDRSZ);

  /* Function internals start here */

  int i;
  UriPathSegmentA* pathseg;
  int quit;
  UriParserStateA parser;
  UriList* uri_list=(UriList*) palloc(sizeof(UriList));
  if (!uri_list) {
    ereport(ERROR,
            (errcode(ERRCODE_OUT_OF_MEMORY),
             errmsg("Memory allocation failed.")));
    PG_RETURN_NULL();
  }
  UriList* uri_list_tail=uri_list;

  char* inp_start=inp; /* Initialization not really necessary */
  unsigned char* inp_finish;

  const char* const character_mask="0000000000000000000000000000000001011111111110111111111111210101111111111111111111111111111101010111111111111111111111111110001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";

  /* this mask describes the legal characters */

  char state=0;

  for (inp_finish=(unsigned char*)inp;*inp_finish;++inp_finish) {
    switch (character_mask[*inp_finish]+state) {
      case '1':
        state=3;
        inp_start=(char*) inp_finish;
        break;
      case '2':
        state=6; /* this will certainly not be a valid URI, but... */
        inp_start=(char*) inp_finish;
        break;
      case '3':
        state=0;
        break;
      case '5':
        state=6;
        break;
      case '6':
        *inp_finish='\0';
        state=0;
        parser.uri=&(uri_list_tail->uri);
        if (uriParseUriA(&parser, inp_start) != URI_SUCCESS) {
          uriFreeUriMembersA(&(uri_list_tail->uri));
        } else if (normalize) {
          if (uriNormalizeSyntaxA(&(uri_list_tail->uri)) != URI_SUCCESS) {
            uriFreeUriMembersA(&(uri_list_tail->uri));
          } else {
            uri_list_tail->uri_text=(char*) palloc(1+inp_finish-(unsigned char*) inp_start);
            if (!uri_list_tail->uri_text) {
              ereport(ERROR,
                      (errcode(ERRCODE_OUT_OF_MEMORY),
                       errmsg("Memory allocation failed.")));
              PG_RETURN_NULL();
            }
            strcpy(uri_list_tail->uri_text,inp_start);
            uri_list_tail->next=(UriList*) palloc(sizeof(UriList));
            if (!uri_list_tail->next) {
              ereport(ERROR,
                      (errcode(ERRCODE_OUT_OF_MEMORY),
                       errmsg("Memory allocation failed.")));
              PG_RETURN_NULL();
            }
            uri_list_tail=uri_list_tail->next;
          }
        } else {
          uri_list_tail->uri_text=(char*) palloc(1+inp_finish-(unsigned char *) inp_start);
          if (!uri_list_tail->uri_text) {
            ereport(ERROR,
                    (errcode(ERRCODE_OUT_OF_MEMORY),
                     errmsg("Memory allocation failed.")));
            PG_RETURN_NULL();
          }
          strcpy(uri_list_tail->uri_text,inp_start);
          uri_list_tail->next=(UriList*) palloc(sizeof(UriList));
          if (!uri_list_tail->next) {
            ereport(ERROR,
                    (errcode(ERRCODE_OUT_OF_MEMORY),
                     errmsg("Memory allocation failed.")));
            PG_RETURN_NULL();
          }
          uri_list_tail=uri_list_tail->next;
        }
        break;
    } 
  }

  if (state==6) {
    parser.uri=&(uri_list_tail->uri);
    if (uriParseUriA(&parser, inp_start) != URI_SUCCESS) {
      uriFreeUriMembersA(&(uri_list_tail->uri));
    } else if (normalize) {
      if (uriNormalizeSyntaxA(&(uri_list_tail->uri)) != URI_SUCCESS) {
        uriFreeUriMembersA(&(uri_list_tail->uri));
      } else {
        uri_list_tail->uri_text=(char*) palloc(1+inp_finish-(unsigned char *) inp_start);
        if (!uri_list_tail->uri_text) {
          ereport(ERROR,
                  (errcode(ERRCODE_OUT_OF_MEMORY),
                   errmsg("Memory allocation failed.")));
          PG_RETURN_NULL();
        }
        strcpy(uri_list_tail->uri_text,inp_start);
        uri_list_tail->next=(UriList*) palloc(sizeof(UriList));
        if (!uri_list_tail->next) {
          ereport(ERROR,
                  (errcode(ERRCODE_OUT_OF_MEMORY),
                   errmsg("Memory allocation failed.")));
          PG_RETURN_NULL();
        }
        uri_list_tail=uri_list_tail->next;
      }
    } else {
      uri_list_tail->uri_text=(char*) palloc(1+inp_finish-(unsigned char *) inp_start);
      if (!uri_list_tail->uri_text) {
        ereport(ERROR,
                (errcode(ERRCODE_OUT_OF_MEMORY),
                 errmsg("Memory allocation failed.")));
        PG_RETURN_NULL();
      }
      strcpy(uri_list_tail->uri_text,inp_start);
      uri_list_tail->next=(UriList*) palloc(sizeof(UriList));
      if (!uri_list_tail->next) {
        ereport(ERROR,
                (errcode(ERRCODE_OUT_OF_MEMORY),
                 errmsg("Memory allocation failed.")));
        PG_RETURN_NULL();
      }
      uri_list_tail=uri_list_tail->next;
    }
  }

  /* Function internals finish here */

  if (get_call_result_type(fcinfo, NULL, &tupledesc) != TYPEFUNC_COMPOSITE) {
    ereport(ERROR,
            (errcode(ERRCODE_FEATURE_NOT_SUPPORTED),
             errmsg("function returning record called in context "
                    "that cannot accept type record")));
    PG_RETURN_NULL();
  }
  /* This error should never happen, because the SQL function is defined
     as returning a uri_type. */

  attinmeta = TupleDescGetAttInMetadata(tupledesc);

  if (uri_list==uri_list_tail) {
    /* empty list */
    char** retval=(char**) palloc(12*sizeof(char*));
    if (!retval) {
      ereport(ERROR,
              (errcode(ERRCODE_OUT_OF_MEMORY),
               errmsg("Memory allocation failed.")));
      PG_RETURN_NULL();
    }
    for(int i=0;i<12;++i) {
      retval[i]=(char*) palloc(3);
      if (!retval[i]) {
        ereport(ERROR,
                (errcode(ERRCODE_OUT_OF_MEMORY),
                 errmsg("Memory allocation failed.")));
        PG_RETURN_NULL();
      }
      memcpy(retval[i],"{}",3);
    }
    HeapTuple tuple;
    Datum result;
  
    tuple=BuildTupleFromCStrings(attinmeta,retval);
    result=HeapTupleGetDatum(tuple);
  
    PG_RETURN_DATUM(result);
  }

  uri_list_tail->next=NULL;

  /*
    Note that the last element on the uri list is a dummy variable.
  */
   
  char** retval=(char**) palloc(12*sizeof(char*));
  if (!retval) {
    ereport(ERROR,
            (errcode(ERRCODE_OUT_OF_MEMORY),
             errmsg("Memory allocation failed.")));
    PG_RETURN_NULL();
  }
  unsigned int sizes[12]={2,2,2,2,2,2,2,2,2,2,2,2};

  for(UriList* urip=uri_list;urip->next!=NULL;urip=urip->next) {
    sizes[0]+=3+2*(urip->uri.scheme.afterLast-urip->uri.scheme.first);
    sizes[1]+=3+2*(urip->uri.userInfo.afterLast-urip->uri.userInfo.first);
    sizes[2]+=3+2*(urip->uri.hostText.afterLast-urip->uri.hostText.first);
    sizes[3]+=3+2*((urip->uri.hostData.ip4!=NULL)<<4);
    sizes[4]+=3+2*((urip->uri.hostData.ip6!=NULL)<<6);
    sizes[5]+=3+2*(urip->uri.hostData.ipFuture.afterLast-urip->uri.hostData.ipFuture.first);
    sizes[6]+=3+2*(urip->uri.portText.afterLast-urip->uri.portText.first);
    /* path handling */
    if (urip->uri.pathHead==NULL) {
      sizes[7]+=3;
    } else {
      pathseg=urip->uri.pathHead;
      do {
        quit=((pathseg==urip->uri.pathTail)||(pathseg->next==NULL));
        sizes[7]+=1+2*(pathseg->text.afterLast-pathseg->text.first);
        pathseg=pathseg->next;
      } while (!quit);
    }
    sizes[8]+=3+2*(urip->uri.query.afterLast-urip->uri.query.first);
    sizes[9]+=3+2*(urip->uri.fragment.afterLast-urip->uri.fragment.first);
    sizes[10]+=6-urip->uri.absolutePath;
    sizes[11]+=3+2*strlen(urip->uri_text);
  }

  char* head[12];
  for(int i=0;i<12;++i) {
    retval[i]=(char*) palloc(sizes[i]);
    if (!retval[i]) {
      ereport(ERROR,
              (errcode(ERRCODE_OUT_OF_MEMORY),
               errmsg("Memory allocation failed.")));
      PG_RETURN_NULL();
    }
    head[i]=retval[i];
    *(head[i])='{';
    ++(head[i]);
  }
  char* buffer=palloc(sizes[7]);
  if (!buffer) {
    ereport(ERROR,
            (errcode(ERRCODE_OUT_OF_MEMORY),
             errmsg("Memory allocation failed.")));
    PG_RETURN_NULL();
  }

  int length;

  for(UriList* urip=uri_list;urip->next!=NULL;urip=urip->next) {
    length=urip->uri.scheme.afterLast-urip->uri.scheme.first;
    head[0]=memenc(head[0],urip->uri.scheme.first,length);
    *(head[0])=',';
    ++(head[0]);

    length=urip->uri.userInfo.afterLast-urip->uri.userInfo.first;
    head[1]=memenc(head[1],urip->uri.userInfo.first,length);
    *(head[1])=',';
    ++(head[1]);

    length=urip->uri.hostText.afterLast-urip->uri.hostText.first;
    head[2]=memenc(head[2],urip->uri.hostText.first,length);
    *(head[2])=',';
    ++(head[2]);

    if (urip->uri.hostData.ip4!=NULL) {
      memcpy(head[3],"\\000\\000\\000\\000",16);
      for(i=0;i<4;++i) {
        ++(head[3]);
        *(head[3])+=urip->uri.hostData.ip4->data[i]>> 6;
        ++(head[3]);
        *(head[3])+=(urip->uri.hostData.ip4->data[i]>> 3)&7;
        ++(head[3]);
        *(head[3])+=urip->uri.hostData.ip4->data[i]&7;
        ++(head[3]);
      }
    } else {
      *(head[3])='"';
      ++(head[3]);
      *(head[3])='"';
      ++(head[3]);
    }
    *(head[3])=',';
    ++(head[3]);

    if (urip->uri.hostData.ip6!=NULL) {
      memcpy(head[4],"\\000\\000\\000\\000\\000\\000\\000\\000\\000\\000\\000\\000\\000\\000\\000\\000",64);
      for(i=0;i<16;++i) {
        ++(head[4]);
        *(head[4])+=urip->uri.hostData.ip6->data[i]>> 6;
        ++(head[4]);
        *(head[4])+=(urip->uri.hostData.ip6->data[i]>> 3)&7;
        ++(head[4]);
        *(head[4])+=urip->uri.hostData.ip6->data[i]&7;
        ++(head[4]);
      }
    } else {
      *(head[4])='"';
      ++(head[4]);
      *(head[4])='"';
      ++(head[4]);
    }
    *(head[4])=',';
    ++(head[4]);

    length=urip->uri.hostData.ipFuture.afterLast-urip->uri.hostData.ipFuture.first;
    head[5]=memenc(head[5],urip->uri.hostData.ipFuture.first,length);
    *(head[5])=',';
    ++(head[5]);

    length=urip->uri.portText.afterLast-urip->uri.portText.first;
    head[6]=memenc(head[6],urip->uri.portText.first,length);
    *(head[6])=',';
    ++(head[6]);

    if (urip->uri.pathHead!=NULL) {
      pathseg=urip->uri.pathHead;
      char* buf_ptr=buffer;
      do {
        quit=((pathseg==urip->uri.pathTail)||(pathseg->next==NULL));
        if (pathseg->text.afterLast!=pathseg->text.first) {
          memcpy(buf_ptr,pathseg->text.first,pathseg->text.afterLast-pathseg->text.first);
          buf_ptr+=pathseg->text.afterLast-pathseg->text.first;
        }
        *buf_ptr='/';
        ++buf_ptr;
        pathseg=pathseg->next;
      } while (!quit);
      --buf_ptr;
      *buf_ptr='\0';
      head[7]=strenc(head[7],buffer);
    } else {
      *(head[7])='"';
      ++(head[7]);
      *(head[7])='"';
      ++(head[7]);
    }
    *(head[7])=',';
    ++(head[7]);

    length=urip->uri.query.afterLast-urip->uri.query.first;
    head[8]=memenc(head[8],urip->uri.query.first,length);
    *(head[8])=',';
    ++(head[8]);

    length=urip->uri.fragment.afterLast-urip->uri.fragment.first;
    head[9]=memenc(head[9],urip->uri.fragment.first,length);
    *(head[9])=',';
    ++(head[9]);

    if (urip->uri.absolutePath) {
      memcpy(head[10],"true,",5);
      head[10]+=5;
    } else {
      memcpy(head[10],"false,",6);
      head[10]+=6;
    }

    length=strlen(urip->uri_text);
    head[11]=memenc(head[11],urip->uri_text,length);
    *(head[11])=',';
    ++(head[11]);
  }

  for(i=0;i<12;++i) {
    *(head[i])='\0';
    --(head[i]);
    *(head[i])='}';
  }

  /* There is no need to call pfree. It's called automatically. */

  HeapTuple tuple;
  Datum result;

  tuple=BuildTupleFromCStrings(attinmeta,retval);
  result=HeapTupleGetDatum(tuple);

  /* Free memory start */
  for(UriList* urip=uri_list;urip->next!=NULL;urip=urip->next) {
    uriFreeUriMembersA(&(urip->uri));
  }
  /* Free memory finish */

  PG_RETURN_DATUM(result);
}
