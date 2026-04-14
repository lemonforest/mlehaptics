#ifndef CS_GZIP_H
#define CS_GZIP_H

#include <stdio.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Open a file for reading with transparent gzip decompression.
 *
 * If the file begins with the gzip magic (1F 8B), its entire contents are
 * decompressed into a tmpfile() and *out is set to that tmpfile, positioned
 * at offset 0 and ready for binary reads. Otherwise *out is the original
 * file, positioned at offset 0.
 *
 * The caller is responsible for fclose()ing *out in both cases (closing a
 * tmpfile also deletes it, so no cleanup is needed for the decompressed
 * copy).
 *
 * Returns 0 on success, non-zero on error. */
int cs_open_read_transparent(const char *path, FILE **out);

/* Compress the full contents of src_plain into dst_path as a gzip file.
 *
 * src_plain is rewound to offset 0 before reading. dst_path is created or
 * truncated. The output conforms to RFC 1952 (single-member gzip stream
 * with CRC32 and ISIZE trailer).
 *
 * Returns 0 on success, non-zero on error. */
int cs_file_write_gzip(const char *dst_path, FILE *src_plain);

#ifdef __cplusplus
}
#endif

#endif /* CS_GZIP_H */
