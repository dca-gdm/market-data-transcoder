#! /usr/bin/env python3
#
# Copyright 2022 Google LLC
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import argparse
import logging
import os

from transcoder.message.MessageParser import MessageParser
from transcoder.message.factory import all_supported_factory_types
from transcoder.source import all_source_identifiers

script_dir = os.path.dirname(__file__)


def main():
    arg_parser = argparse.ArgumentParser(description='Datacast Transcoder process input arguments', allow_abbrev=False)

    source_options_group = arg_parser.add_argument_group('Input source arguments')
    source_options_group.add_argument('--factory', required=True, choices=all_supported_factory_types(),
                                      help='Message factory for decoding')
    source_options_group.add_argument('--schema_file', required=True, type=str, help='Path to the schema file')
    source_options_group.add_argument('--source_file', required=True, type=str, help='Path to the source file')
    source_options_group.add_argument('--source_file_format_type', required=True, choices=all_source_identifiers(),
                                      help='The source file format')
    source_options_group.add_argument('--base64', action='store_true',
                                      help='Indicates if each individual message extracted from '
                                           'the source is base 64 encoded')
    source_options_group.add_argument('--fix_header_tags', type=str, help='Comma delimited list of fix header tags')
    source_options_group.add_argument('--message_handlers', type=str, help='Comma delimited list of message '
                                                                           'handlers in priority order')
    source_options_group.add_argument('--message_skip_bytes', type=int, default=0,
                                      help='Number of bytes to skip before processing individual messages within a '
                                           'repeated '
                                           'length delimited file message source')

    message_filter_group = source_options_group.add_mutually_exclusive_group()
    message_filter_group.add_argument('--message_type_exclusions', type=str,
                                      help='Comma-delimited list of message types to exclude '
                                           'when processing')
    message_filter_group.add_argument('--message_type_inclusions', type=str,
                                      help='Comma-delimited list of message types to include '
                                           'when processing')

    source_options_group.add_argument('--sampling_count', type=int, default=None,
                                      help='To be used for testing only - the sampling count indicates how many of '
                                           'each distinct '
                                           'message type to process, any additional will be skipped')
    source_options_group.add_argument('--skip_bytes', type=int, default=0,
                                      help='Number of bytes to skip before processing the file. Useful for skipping file-level headers')
    source_options_group.add_argument('--skip_lines', type=int, default=0,
                                      help='Number of lines to skip before processing the file')
    source_options_group.add_argument('--source_file_endian', choices=['big', 'little'], default='big',
                                      help='Source file endianness')

    output_options_group = arg_parser.add_argument_group('Output arguments')
    output_options_group.add_argument('--output_path', help='Output file path. Defaults to avroOut')
    output_options_group.add_argument('--output_type', choices=['avro', 'fastavro', 'pubsub', 'bigquery'],
                                      default='fastavro',
                                      help='Output format type')
    output_options_group.add_argument('--error_output_path',
                                      help='Error output file path if --continue_on_error flag enabled. Defaults to errorOut')
    output_options_group.add_argument('--lazy_create_resources', action='store_true',
                                      help='Flag indicating that output resources for message types '
                                           'should be only created as messages of each type are encountered in the source data. Default behavior is to create resources for each message type before messages are processed. Particularly useful when working with FIX but only processing a limited set of message types in the source data')

    gcp_options_group = arg_parser.add_argument_group('Google Cloud arguments')
    gcp_options_group.add_argument('--destination_project_id', help='The Google Cloud project ID for the destination resource')

    bigquery_options_group = arg_parser.add_argument_group('BigQuery arguments')
    bigquery_options_group.add_argument('--destination_dataset_id', help='The BigQuery dataset for the destination. If it does not exist, it will be created')

    pubsub_options_group = arg_parser.add_argument_group('Pub/Sub arguments')
    pubsub_options_group.add_argument('--output_encoding', default='binary', choices=['binary', 'json'],
                                      help='The encoding of the output')
    pubsub_options_group.add_argument('--create_schema_enforcing_topics', type=bool, default=True,
                                      action=argparse.BooleanOptionalAction,
                                      help='Indicates if Pub/Sub schemas should be created and used to validate '
                                           'messages sent to a topic')

    arg_parser.add_argument('--continue_on_error', action='store_true', help='Indicates if an exception file should '
                                                                             'be created, and records continued to be '
                                                                             'processed upon message level '
                                                                             'exceptions')
    arg_parser.add_argument('--log', choices=['notset', 'debug', 'info', 'warning', 'error', 'critical'],
                            default='info',
                            help='The default logging level')
    arg_parser.add_argument('-q', '--quiet', action='store_true', help='Suppress message output to console')
    arg_parser.add_argument('-v', '--version', action='version', version='Datacast Transcoder 1.0.0')

    args = arg_parser.parse_args()

    logging.basicConfig(level=args.log.upper())
    logging.debug(args)

    factory = args.factory
    schema_file_path = os.path.expanduser(args.schema_file)
    source_file_path = os.path.expanduser(args.source_file)
    source_file_format_type = args.source_file_format_type
    source_file_endian = args.source_file_endian
    skip_lines = args.skip_lines
    skip_bytes = args.skip_bytes
    message_skip_bytes = args.message_skip_bytes
    base64 = args.base64
    quiet = args.quiet
    output_type = args.output_type
    output_encoding = args.output_encoding
    output_path = os.path.expanduser(args.output_path) if args.output_path is not None else None
    error_output_path = os.path.expanduser(args.error_output_path) if args.error_output_path is not None else None
    destination_project_id = args.destination_project_id
    destination_dataset_id = args.destination_dataset_id
    message_handlers = args.message_handlers
    lazy_create_resources = args.lazy_create_resources
    continue_on_error = args.continue_on_error
    create_schema_enforcing_topics = args.create_schema_enforcing_topics
    sampling_count = args.sampling_count
    message_type_inclusions = args.message_type_inclusions
    message_type_exclusions = args.message_type_exclusions
    fix_header_tags = args.fix_header_tags

    message_parser = MessageParser(factory, schema_file_path, source_file_path, source_file_format_type,
                                   source_file_endian, skip_lines=skip_lines, skip_bytes=skip_bytes,
                                   message_skip_bytes=message_skip_bytes, is_base_64_encoded=base64,
                                   output_type=output_type, output_path=output_path, output_encoding=output_encoding,
                                   destination_project_id=destination_project_id,
                                   destination_dataset_id=destination_dataset_id,
                                   message_handlers=message_handlers, lazy_create_resources=lazy_create_resources,
                                   continue_on_error=continue_on_error, error_output_path=error_output_path,
                                   quiet=quiet, create_schema_enforcing_topics=create_schema_enforcing_topics,
                                   sampling_count=sampling_count, message_type_inclusions=message_type_inclusions,
                                   message_type_exclusions=message_type_exclusions, fix_header_tags=fix_header_tags)

    message_parser.process()


if __name__ == "__main__":
    main()
