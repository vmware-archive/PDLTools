/**
 * File: sampling.c
 * C backend for "sampling.sql"
 *
 * Functions in this file are internal to the Sampling module. They assume
 * that all checking of input values has already been performed by the
 * functions calling them. They are therefore unsafe to use directly.
 *
 * Function __sampling_prep_grp takes an array and stores it in a format
 * more efficiently accessible. Function __sampling_samp_grp uses this array
 * to perform the necessary per-row procesing, with the idea being that
 * __sampling_samp_grp is written to be as efficient as possible.
 */

#include <postgres.h>
#include <fmgr.h>

#include <funcapi.h>

#include <utils/array.h>
#include <utils/lsyscache.h>


PG_FUNCTION_INFO_V1(__sampling_prep_grp);

Datum __sampling_prep_grp(PG_FUNCTION_ARGS);

Datum __sampling_prep_grp(PG_FUNCTION_ARGS)
{
  ArrayType *arr;
  Datum* elements;
  Oid arr_element_type;
  int16 arr_element_type_width;
  bool arr_element_type_byvalue;
  char arr_element_type_alignment_code;
  bool* nulls;
  
  int32 i,n;
  float8 *rc;
  bytea *buffer;
  if (PG_ARGISNULL(0)) {
    PG_RETURN_NULL();
  }
  arr=PG_GETARG_ARRAYTYPE_P(0);
  // CHECKARRVALID(arr); // Checks if any elements are NULL.
  if (ARR_NDIM(arr) != 1) {
    PG_RETURN_NULL();
  }
  // n=(ARR_DIMS(arr))[0];

  arr_element_type = ARR_ELEMTYPE(arr);
  if (arr_element_type != FLOAT8OID) {
    PG_RETURN_NULL();
  }
  get_typlenbyvalalign(arr_element_type, &arr_element_type_width,
    &arr_element_type_byvalue, &arr_element_type_alignment_code);
  deconstruct_array(arr,arr_element_type,arr_element_type_width,
    arr_element_type_byvalue, arr_element_type_alignment_code,
    &elements,&nulls,&n);

  buffer=(bytea*) palloc(VARHDRSZ+n*sizeof(float8));
  SET_VARSIZE(buffer,VARHDRSZ+n*sizeof(float8));
  rc=(float8*) VARDATA(buffer);

  // p = ARRPTR(arr);
  for(i=0;i<n;++i) {
    if (nulls[i]) {
      PG_RETURN_NULL();
    } else {
      rc[i]=DatumGetFloat8(elements[i]);
    }
  }
  PG_RETURN_BYTEA_P(buffer);
}

PG_FUNCTION_INFO_V1(__sampling_samp_grp);

Datum __sampling_samp_grp(PG_FUNCTION_ARGS);

Datum __sampling_samp_grp(PG_FUNCTION_ARGS)
{
  // Function is meant to be called only from the sampling module, which
  // already performs all error checks. Furthermore, PL/C wrapping is defined
  // as STRICT. Absolutely no checks here.
  float8 val;
  bytea* buffer;
  float8* arr;
  float8* arr_end;
  int32 rc;

  val = PG_GETARG_FLOAT8(0);
  buffer = PG_GETARG_BYTEA_P(1);
  arr = (float8*) ((char*)buffer+VARHDRSZ);
  arr_end = (float8*) ((char*)buffer+VARSIZE(buffer));
  rc=0;
  for (; arr!=arr_end; ++arr) {
    rc+=(*arr < val);
  }
  PG_RETURN_INT32(rc);
}
