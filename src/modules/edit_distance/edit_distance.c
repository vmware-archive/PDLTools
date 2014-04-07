/**
 * File: edit_distance.c
 * C backend for "edit_distance.sql"
 */

#include <postgres.h>
#include <fmgr.h>
#include <sys/time.h>

#include <funcapi.h>

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#define min(a,b) ((a)<(b)?(a):(b))

int edit_distance_unsafe_impl13(const unsigned char* const str1,
  unsigned int lstr1,
  const unsigned char* const str2,
  unsigned int lstr2,
  unsigned int ins_cost, unsigned int del_cost, unsigned int sub_cost,
  unsigned int tp_cost, unsigned int final_tp_cost,
  unsigned int spec_sub_cost, const unsigned char* const spec_sub_from,
  const unsigned char* const spec_sub_to, unsigned int lspec_sub);


int edit_distance_unsafe_impl13(const unsigned char* const str1,
  unsigned int lstr1,
  const unsigned char* const str2,
  unsigned int lstr2,
  unsigned int ins_cost, unsigned int del_cost, unsigned int sub_cost,
  unsigned int tp_cost, unsigned int final_tp_cost,
  unsigned int spec_sub_cost, const unsigned char* const spec_sub_from,
  const unsigned char* const spec_sub_to, unsigned int lspec_sub)
{
  unsigned int *costs;
  unsigned int last_seen1[256];
  unsigned int last_seen2;
  unsigned char spec_bitmap[8192];
  unsigned int i1, i2;
  unsigned int rc, ins_step, del_step, tp_step, sub_step;
  const unsigned int INFTY = lstr1*del_cost+lstr2*ins_cost;

  memset(spec_bitmap,0,8192);
  for(i1=0;i1!=lspec_sub;++i1) {
    spec_bitmap[(spec_sub_from[i1]>>3)+
                (((unsigned int)(spec_sub_to[i1]))<<5)]|=
      (1<<((spec_sub_from[i1])&7));
  }
 
  costs = (unsigned int*) malloc ((lstr1+2)*(lstr2+2)*sizeof(unsigned int));

  costs[0]=INFTY;
  costs[lstr1+2]=INFTY;
  for(i1 = 1; i1 < lstr1+2; ++i1) {
    costs[i1]=INFTY;
    costs[lstr1+2+i1]=(i1-1)*del_cost;
  }

  memset(last_seen1,0,256*sizeof(int));
  for(i2 = 2; i2 < lstr2+2; ++i2) {
    costs[(lstr1+2)*i2]=INFTY;
    costs[(lstr1+2)*i2+1]=(i2-1)*ins_cost;
    last_seen2=0;
    for(i1 = 2; i1 < lstr1+2; ++i1) {
      if (str1[i1-2]==str2[i2-2]) {
        sub_step=costs[(lstr1+2)*(i2-1)+(i1-1)];
      } else if (spec_bitmap[(str1[i1-2]>>3)+(((unsigned int)(str2[i2-2]))<<5)]
                 >>(str1[i1-2]&7)) {
        sub_step=costs[(lstr1+2)*(i2-1)+(i1-1)]+spec_sub_cost;
      } else {
        sub_step=costs[(lstr1+2)*(i2-1)+(i1-1)]+sub_cost;
      }

      del_step=costs[(lstr1+2)*i2+(i1-1)]+del_cost;

      ins_step=costs[(lstr1+2)*(i2-1)+i1]+ins_cost;
      
      if ((i1-last_seen2==2)&&(i2-last_seen1[str1[i1-2]]==2)) {
        tp_step=costs[(lstr1+2)*(i2-2)+(i1-2)]+final_tp_cost;
      } else {
        tp_step=costs[(lstr1+2)*(last_seen1[str1[i1-2]])+last_seen2]+
                  tp_cost+(i1-last_seen2-2)*del_cost+
                  (i2-last_seen1[str1[i1-2]]-2)*ins_cost;
      }

      costs[(lstr1+2)*i2+i1]=min(min(del_step,ins_step),min(sub_step,tp_step));

      if (str1[i1-2]==str2[i2-2]) {
        last_seen2=i1-1;
      }
    }
    last_seen1[str2[i2-2]]=i2-1;
  }

  rc=costs[(lstr1+2)*(lstr2+2)-1];

  free(costs);
 
  return rc;
}

PG_FUNCTION_INFO_V1(edit_distance_unsafe13);

Datum edit_distance_unsafe13(PG_FUNCTION_ARGS);

Datum edit_distance_unsafe13(PG_FUNCTION_ARGS)
{
  text* str1_text=PG_GETARG_TEXT_P(0);
  unsigned int lstr1=VARSIZE(str1_text)-VARHDRSZ;
  text* str2_text=PG_GETARG_TEXT_P(1);
  unsigned int lstr2=VARSIZE(str2_text)-VARHDRSZ;
    /* Function is defined STRICT in SQL, so no NULL check is needed. */
  unsigned int ins_cost=PG_GETARG_INT32(2);
  unsigned int del_cost=PG_GETARG_INT32(3);
  unsigned int sub_cost=PG_GETARG_INT32(4);
  unsigned int tp_cost=PG_GETARG_INT32(5);
  unsigned int final_tp_cost=PG_GETARG_INT32(6);
  unsigned int spec_sub_cost=PG_GETARG_INT32(7);
  text* spec_sub_from_text=PG_GETARG_TEXT_P(8);
  text* spec_sub_to_text=PG_GETARG_TEXT_P(9);
  unsigned int lspec_sub=
    min(VARSIZE(spec_sub_from_text),VARSIZE(spec_sub_to_text))-VARHDRSZ;

  unsigned int rc=edit_distance_unsafe_impl13(
    (const unsigned char* const)VARDATA(str1_text),lstr1,
    (const unsigned char* const)VARDATA(str2_text),lstr2,
    ins_cost,del_cost,sub_cost,tp_cost,final_tp_cost,spec_sub_cost,
    (const unsigned char* const)VARDATA(spec_sub_from_text),
    (const unsigned char* const)VARDATA(spec_sub_to_text),lspec_sub);

  PG_RETURN_INT32(rc);
}


PG_FUNCTION_INFO_V1(edit_distance13);

Datum edit_distance13(PG_FUNCTION_ARGS);

Datum edit_distance13(PG_FUNCTION_ARGS)
{
  text* str1_text=PG_GETARG_TEXT_P(0);
  unsigned int lstr1=VARSIZE(str1_text)-VARHDRSZ;
  text* str2_text=PG_GETARG_TEXT_P(1);
  unsigned int lstr2=VARSIZE(str2_text)-VARHDRSZ;
    /* Function is defined STRICT in SQL, so no NULL check is needed. */
  unsigned int ins_cost=PG_GETARG_INT32(2);
  unsigned int del_cost=PG_GETARG_INT32(3);
  unsigned int sub_cost=PG_GETARG_INT32(4);
  unsigned int tp_cost=PG_GETARG_INT32(5);
  unsigned int final_tp_cost=PG_GETARG_INT32(6);
  unsigned int spec_sub_cost=PG_GETARG_INT32(7);
  text* spec_sub_from_text=PG_GETARG_TEXT_P(8);
  text* spec_sub_to_text=PG_GETARG_TEXT_P(9);
  unsigned int lspec_sub=
    min(VARSIZE(spec_sub_from_text),VARSIZE(spec_sub_to_text))-VARHDRSZ;
  unsigned int rc;

  if (final_tp_cost>tp_cost) {
    ereport(ERROR,
            (errcode(ERRCODE_FEATURE_NOT_SUPPORTED),
            errmsg("Function must be called with final_tp_cost <= tp_cost")));
    PG_RETURN_NULL();
  }

  if (ins_cost+del_cost>2*final_tp_cost) {
    ereport(ERROR,
            (errcode(ERRCODE_FEATURE_NOT_SUPPORTED),
            errmsg("Function must be called with "
                   "ins_cost+del_cost <= 2*final_tp_cost")));
    PG_RETURN_NULL();
  }

  if ((sub_cost>final_tp_cost)||(spec_sub_cost>final_tp_cost)) {
    ereport(ERROR,
            (errcode(ERRCODE_FEATURE_NOT_SUPPORTED),
            errmsg("Function must be called with "
                   "max(sub_cost,spec_sub_cost) <= final_tp_cost")));
    PG_RETURN_NULL();
  }

  rc=edit_distance_unsafe_impl13(
    (const unsigned char* const)VARDATA(str1_text),lstr1,
    (const unsigned char* const)VARDATA(str2_text),lstr2,
    ins_cost,del_cost,sub_cost,tp_cost,final_tp_cost,spec_sub_cost,
    (const unsigned char* const)VARDATA(spec_sub_from_text),
    (const unsigned char* const)VARDATA(spec_sub_to_text),lspec_sub);

  PG_RETURN_INT32(rc);
}


int edit_distance_unsafe_impl9(const unsigned char* const str1,
  unsigned int lstr1,
  const unsigned char* const str2,
  unsigned int lstr2,
  unsigned int ins_cost, unsigned int del_cost, unsigned int sub_cost,
  unsigned int tp_cost, unsigned int final_tp_cost);


int edit_distance_unsafe_impl9(const unsigned char* const str1,
  unsigned int lstr1,
  const unsigned char* const str2,
  unsigned int lstr2,
  unsigned int ins_cost, unsigned int del_cost, unsigned int sub_cost,
  unsigned int tp_cost, unsigned int final_tp_cost)
{
  unsigned int *costs;
  unsigned int last_seen1[256];
  unsigned int last_seen2;
  unsigned int i1, i2;
  unsigned int rc, ins_step, del_step, tp_step, sub_step;
  const unsigned int INFTY = lstr1*del_cost+lstr2*ins_cost;

  costs = (unsigned int*) malloc ((lstr1+2)*(lstr2+2)*sizeof(unsigned int));

  costs[0]=INFTY;
  costs[lstr1+2]=INFTY;
  for(i1 = 1; i1 < lstr1+2; ++i1) {
    costs[i1]=INFTY;
    costs[lstr1+2+i1]=(i1-1)*del_cost;
  }

  memset(last_seen1,0,256*sizeof(int));
  for(i2 = 2; i2 < lstr2+2; ++i2) {
    costs[(lstr1+2)*i2]=INFTY;
    costs[(lstr1+2)*i2+1]=(i2-1)*ins_cost;
    last_seen2=0;
    for(i1 = 2; i1 < lstr1+2; ++i1) {
      if (str1[i1-2]==str2[i2-2]) {
        sub_step=costs[(lstr1+2)*(i2-1)+(i1-1)];
      } else {
        sub_step=costs[(lstr1+2)*(i2-1)+(i1-1)]+sub_cost;
      }

      del_step=costs[(lstr1+2)*i2+(i1-1)]+del_cost;

      ins_step=costs[(lstr1+2)*(i2-1)+i1]+ins_cost;
      
      if ((i1-last_seen2==2)&&(i2-last_seen1[str1[i1-2]]==2)) {
        tp_step=costs[(lstr1+2)*(i2-2)+(i1-2)]+final_tp_cost;
      } else {
        tp_step=costs[(lstr1+2)*(last_seen1[str1[i1-2]])+last_seen2]+
                  tp_cost+(i1-last_seen2-2)*del_cost+
                  (i2-last_seen1[str1[i1-2]]-2)*ins_cost;
      }

      costs[(lstr1+2)*i2+i1]=min(min(del_step,ins_step),min(sub_step,tp_step));

      if (str1[i1-2]==str2[i2-2]) {
        last_seen2=i1-1;
      }
    }
    last_seen1[str2[i2-2]]=i2-1;
  }

  rc=costs[(lstr1+2)*(lstr2+2)-1];

  free(costs);
 
  return rc;
}

PG_FUNCTION_INFO_V1(edit_distance_unsafe9);

Datum edit_distance_unsafe9(PG_FUNCTION_ARGS);

Datum edit_distance_unsafe9(PG_FUNCTION_ARGS)
{
  text* str1_text=PG_GETARG_TEXT_P(0);
  unsigned int lstr1=VARSIZE(str1_text)-VARHDRSZ;
  text* str2_text=PG_GETARG_TEXT_P(1);
  unsigned int lstr2=VARSIZE(str2_text)-VARHDRSZ;
    /* Function is defined STRICT in SQL, so no NULL check is needed. */
  unsigned int ins_cost=PG_GETARG_INT32(2);
  unsigned int del_cost=PG_GETARG_INT32(3);
  unsigned int sub_cost=PG_GETARG_INT32(4);
  unsigned int tp_cost=PG_GETARG_INT32(5);
  unsigned int final_tp_cost=PG_GETARG_INT32(6);

  unsigned int rc=edit_distance_unsafe_impl9(
    (const unsigned char* const)VARDATA(str1_text),lstr1,
    (const unsigned char* const)VARDATA(str2_text),lstr2,
    ins_cost,del_cost,sub_cost,tp_cost,final_tp_cost);

  PG_RETURN_INT32(rc);
}


PG_FUNCTION_INFO_V1(edit_distance9);

Datum edit_distance9(PG_FUNCTION_ARGS);

Datum edit_distance9(PG_FUNCTION_ARGS)
{
  text* str1_text=PG_GETARG_TEXT_P(0);
  unsigned int lstr1=VARSIZE(str1_text)-VARHDRSZ;
  text* str2_text=PG_GETARG_TEXT_P(1);
  unsigned int lstr2=VARSIZE(str2_text)-VARHDRSZ;
    /* Function is defined STRICT in SQL, so no NULL check is needed. */
  unsigned int ins_cost=PG_GETARG_INT32(2);
  unsigned int del_cost=PG_GETARG_INT32(3);
  unsigned int sub_cost=PG_GETARG_INT32(4);
  unsigned int tp_cost=PG_GETARG_INT32(5);
  unsigned int final_tp_cost=PG_GETARG_INT32(6);
  unsigned int rc;

  if (final_tp_cost>tp_cost) {
    ereport(ERROR,
            (errcode(ERRCODE_FEATURE_NOT_SUPPORTED),
            errmsg("Function must be called with final_tp_cost <= tp_cost")));
    PG_RETURN_NULL();
  }

  if (ins_cost+del_cost>2*final_tp_cost) {
    ereport(ERROR,
            (errcode(ERRCODE_FEATURE_NOT_SUPPORTED),
            errmsg("Function must be called with "
                   "ins_cost+del_cost <= 2*final_tp_cost")));
    PG_RETURN_NULL();
  }

  if (sub_cost>final_tp_cost) {
    ereport(ERROR,
            (errcode(ERRCODE_FEATURE_NOT_SUPPORTED),
            errmsg("Function must be called with "
                   "sub_cost <= final_tp_cost")));
    PG_RETURN_NULL();
  }

  rc=edit_distance_unsafe_impl9(
    (const unsigned char* const)VARDATA(str1_text),lstr1,
    (const unsigned char* const)VARDATA(str2_text),lstr2,
    ins_cost,del_cost,sub_cost,tp_cost,final_tp_cost);

  PG_RETURN_INT32(rc);
}


PG_FUNCTION_INFO_V1(edit_distance_unsafe8);

Datum edit_distance_unsafe8(PG_FUNCTION_ARGS);

Datum edit_distance_unsafe8(PG_FUNCTION_ARGS)
{
  text* str1_text=PG_GETARG_TEXT_P(0);
  unsigned int lstr1=VARSIZE(str1_text)-VARHDRSZ;
  text* str2_text=PG_GETARG_TEXT_P(1);
  unsigned int lstr2=VARSIZE(str2_text)-VARHDRSZ;
    /* Function is defined STRICT in SQL, so no NULL check is needed. */
  unsigned int ins_cost=PG_GETARG_INT32(2);
  unsigned int del_cost=PG_GETARG_INT32(3);
  unsigned int sub_cost=PG_GETARG_INT32(4);
  unsigned int tp_cost=PG_GETARG_INT32(5);

  unsigned int rc=edit_distance_unsafe_impl9(
    (const unsigned char* const)VARDATA(str1_text),lstr1,
    (const unsigned char* const)VARDATA(str2_text),lstr2,
    ins_cost,del_cost,sub_cost,tp_cost,tp_cost);

  PG_RETURN_INT32(rc);
}


PG_FUNCTION_INFO_V1(edit_distance8);

Datum edit_distance8(PG_FUNCTION_ARGS);

Datum edit_distance8(PG_FUNCTION_ARGS)
{
  text* str1_text=PG_GETARG_TEXT_P(0);
  unsigned int lstr1=VARSIZE(str1_text)-VARHDRSZ;
  text* str2_text=PG_GETARG_TEXT_P(1);
  unsigned int lstr2=VARSIZE(str2_text)-VARHDRSZ;
    /* Function is defined STRICT in SQL, so no NULL check is needed. */
  unsigned int ins_cost=PG_GETARG_INT32(2);
  unsigned int del_cost=PG_GETARG_INT32(3);
  unsigned int sub_cost=PG_GETARG_INT32(4);
  unsigned int tp_cost=PG_GETARG_INT32(5);
  unsigned int rc;

  if (ins_cost+del_cost>2*tp_cost) {
    ereport(ERROR,
            (errcode(ERRCODE_FEATURE_NOT_SUPPORTED),
            errmsg("Function must be called with "
                   "ins_cost+del_cost <= 2*tp_cost")));
    PG_RETURN_NULL();
  }

  if (sub_cost>tp_cost) {
    ereport(ERROR,
            (errcode(ERRCODE_FEATURE_NOT_SUPPORTED),
            errmsg("Function must be called with "
                   "sub_cost <= tp_cost")));
    PG_RETURN_NULL();
  }

  rc=edit_distance_unsafe_impl9(
    (const unsigned char* const)VARDATA(str1_text),lstr1,
    (const unsigned char* const)VARDATA(str2_text),lstr2,
    ins_cost,del_cost,sub_cost,tp_cost,tp_cost);

  PG_RETURN_INT32(rc);
}


int edit_distance_impl7(const unsigned char* const str1,
  unsigned int lstr1,
  const unsigned char* const str2,
  unsigned int lstr2,
  unsigned int ins_cost, unsigned int del_cost, unsigned int sub_cost);


int edit_distance_impl7(const unsigned char* const str1,
  unsigned int lstr1,
  const unsigned char* const str2,
  unsigned int lstr2,
  unsigned int ins_cost, unsigned int del_cost, unsigned int sub_cost)
{
  unsigned int *costs;
  unsigned int i1, i2;
  unsigned int rc, ins_step, del_step, sub_step;
  const unsigned int INFTY = lstr1*del_cost+lstr2*ins_cost;

  costs = (unsigned int*) malloc ((lstr1+2)*(lstr2+2)*sizeof(unsigned int));

  costs[0]=INFTY;
  costs[lstr1+2]=INFTY;
  for(i1 = 1; i1 < lstr1+2; ++i1) {
    costs[i1]=INFTY;
    costs[lstr1+2+i1]=(i1-1)*del_cost;
  }

  for(i2 = 2; i2 < lstr2+2; ++i2) {
    costs[(lstr1+2)*i2]=INFTY;
    costs[(lstr1+2)*i2+1]=(i2-1)*ins_cost;
    for(i1 = 2; i1 < lstr1+2; ++i1) {
      if (str1[i1-2]==str2[i2-2]) {
        sub_step=costs[(lstr1+2)*(i2-1)+(i1-1)];
      } else {
        sub_step=costs[(lstr1+2)*(i2-1)+(i1-1)]+sub_cost;
      }

      del_step=costs[(lstr1+2)*i2+(i1-1)]+del_cost;

      ins_step=costs[(lstr1+2)*(i2-1)+i1]+ins_cost;
      
      costs[(lstr1+2)*i2+i1]=min(min(del_step,ins_step),sub_step);

    }
  }

  rc=costs[(lstr1+2)*(lstr2+2)-1];

  free(costs);
 
  return rc;
}

PG_FUNCTION_INFO_V1(edit_distance7);

Datum edit_distance7(PG_FUNCTION_ARGS);

Datum edit_distance7(PG_FUNCTION_ARGS)
{
  text* str1_text=PG_GETARG_TEXT_P(0);
  unsigned int lstr1=VARSIZE(str1_text)-VARHDRSZ;
  text* str2_text=PG_GETARG_TEXT_P(1);
  unsigned int lstr2=VARSIZE(str2_text)-VARHDRSZ;
    /* Function is defined STRICT in SQL, so no NULL check is needed. */
  unsigned int ins_cost=PG_GETARG_INT32(2);
  unsigned int del_cost=PG_GETARG_INT32(3);
  unsigned int sub_cost=PG_GETARG_INT32(4);

  unsigned int rc=edit_distance_impl7(
    (const unsigned char* const)VARDATA(str1_text),lstr1,
    (const unsigned char* const)VARDATA(str2_text),lstr2,
    ins_cost,del_cost,sub_cost);

  PG_RETURN_INT32(rc);
}


PG_FUNCTION_INFO_V1(edit_distance6);

Datum edit_distance6(PG_FUNCTION_ARGS);

Datum edit_distance6(PG_FUNCTION_ARGS)
{
  text* str1_text=PG_GETARG_TEXT_P(0);
  unsigned int lstr1=VARSIZE(str1_text)-VARHDRSZ;
  text* str2_text=PG_GETARG_TEXT_P(1);
  unsigned int lstr2=VARSIZE(str2_text)-VARHDRSZ;
    /* Function is defined STRICT in SQL, so no NULL check is needed. */
  unsigned int ins_cost=PG_GETARG_INT32(2);
  unsigned int del_cost=PG_GETARG_INT32(3);

  unsigned int rc=edit_distance_impl7(
    (const unsigned char* const)VARDATA(str1_text),lstr1,
    (const unsigned char* const)VARDATA(str2_text),lstr2,
    ins_cost,del_cost,ins_cost+del_cost);

  PG_RETURN_INT32(rc);
}


PG_FUNCTION_INFO_V1(levenshtein_distance);

Datum levenshtein_distance(PG_FUNCTION_ARGS);

Datum levenshtein_distance(PG_FUNCTION_ARGS)
{
  text* str1_text=PG_GETARG_TEXT_P(0);
  unsigned int lstr1=VARSIZE(str1_text)-VARHDRSZ;
  text* str2_text=PG_GETARG_TEXT_P(1);
  unsigned int lstr2=VARSIZE(str2_text)-VARHDRSZ;
    /* Function is defined STRICT in SQL, so no NULL check is needed. */

  unsigned int rc=edit_distance_impl7(
    (const unsigned char* const)VARDATA(str1_text),lstr1,
    (const unsigned char* const)VARDATA(str2_text),lstr2,
    1,1,1);

  PG_RETURN_INT32(rc);
}


PG_FUNCTION_INFO_V1(demerau_levenshtein_distance);

Datum demerau_levenshtein_distance(PG_FUNCTION_ARGS);

Datum demerau_levenshtein_distance(PG_FUNCTION_ARGS)
{
  text* str1_text=PG_GETARG_TEXT_P(0);
  unsigned int lstr1=VARSIZE(str1_text)-VARHDRSZ;
  text* str2_text=PG_GETARG_TEXT_P(1);
  unsigned int lstr2=VARSIZE(str2_text)-VARHDRSZ;
    /* Function is defined STRICT in SQL, so no NULL check is needed. */

  unsigned int rc=edit_distance_unsafe_impl9(
    (const unsigned char* const)VARDATA(str1_text),lstr1,
    (const unsigned char* const)VARDATA(str2_text),lstr2,
    1,1,1,1,1);

  PG_RETURN_INT32(rc);
}


PG_FUNCTION_INFO_V1(optimal_alignment_distance);

Datum optimal_alignment_distance(PG_FUNCTION_ARGS);

Datum optimal_alignment_distance(PG_FUNCTION_ARGS)
{
  text* str1_text=PG_GETARG_TEXT_P(0);
  unsigned int lstr1=VARSIZE(str1_text)-VARHDRSZ;
  text* str2_text=PG_GETARG_TEXT_P(1);
  unsigned int lstr2=VARSIZE(str2_text)-VARHDRSZ;
    /* Function is defined STRICT in SQL, so no NULL check is needed. */
  const unsigned int INFTY = (lstr1+lstr2);

  unsigned int rc=edit_distance_unsafe_impl9(
    (const unsigned char* const)VARDATA(str1_text),lstr1,
    (const unsigned char* const)VARDATA(str2_text),lstr2,
    1,1,1,INFTY,1);

  PG_RETURN_INT32(rc);
}

