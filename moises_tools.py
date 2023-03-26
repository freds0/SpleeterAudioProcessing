#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import argparse
from glob import glob
import requests
import urllib.request
from os.path import join, exists, basename
from os import makedirs
from tqdm import tqdm
import time


class MoisesAPI:
    '''
    Class that encapsulates the Moises API functions
    '''

    def __init__(self, moises_id, audio_format='flac', waiting_time=5, verbose=1):
        self.moises_id = moises_id
        self.audio_format = audio_format
        self.waiting_time = waiting_time
        self.verbose = verbose


    def get_response(self, job_id):
        '''
        Get information and results of an existing job
        '''
        url = "https://developer-api.moises.ai/api/job/{}".format(job_id)
        headers = {"Authorization": self.moises_id}
        response = requests.request("GET", url, headers=headers)
        return response
    

    def get_job_result(self, job_id):
        '''
        Get information and results of an existing job
        '''
        # Get response
        while True:
            status_response = self.get_response(job_id)

            if status_response.json()['status'] == 'SUCCEEDED':
                if self.verbose > 1: print("------> Job succeeded...")
                return status_response
            elif status_response.json()['status'] == 'FAILED':
                if self.verbose > 1: print("------> Job failed...")
                return False
            else:
                if self.verbose > 1: print("------> Waiting response...")
                time.sleep(int(self.waiting_time))


    def request_url(self):
        '''
        Request our uploadUrl and a downloadUrl:
        '''
        url = "https://developer-api.moises.ai/api/upload"
        headers = {"Authorization": self.moises_id}
        request_url_response = requests.request("GET", url, headers=headers)
        return request_url_response


    def upload_file(self, request_url_response, audio_filepath):

        url = request_url_response.json()['uploadUrl']
        headers = {"content-type": "multipart/form-data"}
        upload_response = requests.request("PUT", url, data=open(audio_filepath, 'rb'), headers=headers)
        return upload_response


    def start_new_job(self, filename, upload_response):
        '''
        Submit a new job to be processed
        '''
        url = "https://developer-api.moises.ai/api/job"
        payload = {
            "name": filename,
            "workflow": "Source-separation-2",
            "params": {"inputUrl": upload_response.json()['downloadUrl']}
        }
        headers = {
            "Authorization": self.moises_id,
            "Content-Type": "application/json"
        }
        job_response = requests.request("POST", url, json=payload, headers=headers)
        return job_response


    def save_results(self, response, output_filepath, lyrics_filepath):
        # Get results links
        vocals_link = response.json()['result']['Vocals']
        transcriptions_link = response.json()['result']['Transcriptions']

        # Saving audio result to file
        urllib.request.urlretrieve(vocals_link, output_filepath)

        # Saving transcription result to file
        urllib.request.urlretrieve(transcriptions_link, lyrics_filepath)
        return True
    
        
    def process_file(self, audio_filepath, output_filepath, lyrics_filepath):
        if self.verbose > 1: print("------> Requesting URL...")
        request_url_response = self.request_url()  

        if self.verbose > 1: print("------> Uploading file...")
        upload_response = self.upload_file(request_url_response, audio_filepath)

        if self.verbose > 1: print("------> Starting job...")
        job_response = self.start_new_job(basename(audio_filepath), request_url_response)

        if self.verbose > 1: print("------> Getting results...")
        response = self.get_job_result(job_response.json()['id'])

        if response:
            if self.verbose > 1: print("------> Saving results...")
            return self.save_results(response, output_filepath, lyrics_filepath)
        else:
            return False


    def process_folder(self, input_dir, output_dir):
        if not exists(output_dir): 
            makedirs(output_dir)

        for audio_filepath in tqdm(glob(input_dir + "/*.{}".format(self.audio_format))):

            if self.verbose: print("----> Processing file using MOISES api: {}".format(basename(audio_filepath)))
            filename = basename(audio_filepath).replace('.{}'.format(self.audio_format), '').replace(' ', '_')
            output_filepath = join(output_dir, filename + '.{}'.format(self.audio_format))
            lyrics_filepath = join(output_dir, filename + '.json')

            if exists(output_filepath):
                if self.verbose: print("------> File already processed: {}".format(basename(filename)))
                continue
            if not(self.process_file(audio_filepath, output_filepath, lyrics_filepath)):
                if self.verbose: print("------> Error processing file: {}".format(basename(filename)))
                continue

        return True


def main():

    parser = argparse.ArgumentParser('Extract vocals and transcriptions from music files using MOISES API')
    parser.add_argument('-i', '--input', default='input', help='Input folder.')
    parser.add_argument('-o', '--output', default='output', help='Output folder.')
    parser.add_argument('--audio_format', default='flac', help='Audio file extensions: wav, flac, mp3.')
    parser.add_argument('--waiting_time', default=5, type=int, help='Waiting time in seconds.')
    parser.add_argument('--verbose', default=1, help="Verbosity level: 0, 1 or 2.")
    parser.add_argument('--moises_id', default='5f9c1b0b-8c1c-4b5e-9c1b-0b8c1c8b5e9c')
    args = parser.parse_args()

    moises_api = MoisesAPI(args.moises_id, args.audio_format, args.waiting_time, args.verbose)
    moises_api.process_folder(args.input, args.output)


if __name__ == "__main__":
    main()        