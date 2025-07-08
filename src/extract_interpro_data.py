#!/usr/bin/env python3
"""
UniProt to InterProScan Pipeline

This script:
1. Reads UniProt IDs from a text file
2. Fetches protein sequences from UniProt
3. Submits sequences to InterProScan web service
4. Retrieves results and saves as JSON files

Usage:
    python interproscan_pipeline.py input_file.txt output_folder/ your_email@example.com

Input file format:
    One UniProt ID per line (e.g., P12345)
"""

import requests
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
import concurrent.futures
import threading

class InterProScanPipeline:
    def __init__(self, output_dir: str = "interproscan_results", email: str = None):
        self.uniprot_base_url = "https://rest.uniprot.org/uniprotkb/"
        self.interproscan_base_url = "https://www.ebi.ac.uk/Tools/services/rest/iprscan5"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.email = email
        
        # Create subdirectories
        (self.output_dir / "sequences").mkdir(exist_ok=True)
        (self.output_dir / "interproscan_results").mkdir(exist_ok=True)
        
        # Thread-safe statistics
        self.lock = threading.Lock()
        self.stats = {
            'total': 0,
            'sequences_fetched': 0,
            'interproscan_submitted': 0,
            'interproscan_completed': 0,
            'failed': 0,
            'errors': []
        }
    
    def add_error(self, error: str):
        """Thread-safe error logging"""
        with self.lock:
            self.stats['errors'].append(error)
    
    def increment_stat(self, stat_name: str):
        """Thread-safe stat increment"""
        with self.lock:
            self.stats[stat_name] += 1
    
    def fetch_uniprot_sequence(self, uniprot_id: str) -> Optional[Tuple[str, str]]:
        """
        Fetch protein sequence from UniProt
        
        Args:
            uniprot_id: UniProt identifier
            
        Returns:
            Tuple of (sequence, description) or None if failed
        """
        try:
            print(f"📥 Fetching sequence for {uniprot_id}...")
            url = f"{self.uniprot_base_url}{uniprot_id}.fasta"
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                fasta_content = response.text.strip()
                lines = fasta_content.split('\n')
                
                if len(lines) >= 2:
                    description = lines[0][1:]  # Remove '>' from header
                    sequence = ''.join(lines[1:])  # Join all sequence lines
                    
                    print(f"✅ Successfully fetched sequence for {uniprot_id} ({len(sequence)} residues)")
                    self.increment_stat('sequences_fetched')
                    return sequence, description
                else:
                    print(f"❌ Invalid FASTA format for {uniprot_id}")
                    self.add_error(f"{uniprot_id}: Invalid FASTA format")
                    return None
            else:
                print(f"❌ Failed to fetch sequence for {uniprot_id}: HTTP {response.status_code}")
                self.add_error(f"{uniprot_id}: UniProt fetch failed - HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching sequence for {uniprot_id}: {e}")
            self.add_error(f"{uniprot_id}: UniProt fetch error - {str(e)}")
            return None
    
    def submit_to_interproscan(self, uniprot_id: str, sequence: str) -> Optional[str]:
        """
        Submit sequence to InterProScan web service
        
        Args:
            uniprot_id: UniProt identifier
            sequence: Protein sequence
            
        Returns:
            Job ID if successful, None otherwise
        """
        try:
            print(f"🔄 Submitting {uniprot_id} to InterProScan...")
            
            # Prepare submission data
            params = {
                'email': self.email,
                'sequence': sequence,
                'format': 'json',
                'goterms': 'true',
                'pathways': 'true'
            }
            
            # Submit job
            response = requests.post(
                f"{self.interproscan_base_url}/run",
                data=params,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=60
            )
            
            if response.status_code == 200:
                job_id = response.text.strip()
                print(f"✅ InterProScan job submitted for {uniprot_id}: {job_id}")
                self.increment_stat('interproscan_submitted')
                return job_id
            else:
                print(f"❌ Failed to submit {uniprot_id} to InterProScan: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                self.add_error(f"{uniprot_id}: InterProScan submission failed - HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error submitting {uniprot_id} to InterProScan: {e}")
            self.add_error(f"{uniprot_id}: InterProScan submission error - {str(e)}")
            return None
    
    def check_job_status(self, job_id: str) -> str:
        """
        Check InterProScan job status
        
        Args:
            job_id: InterProScan job ID
            
        Returns:
            Job status ('RUNNING', 'FINISHED', 'ERROR', etc.)
        """
        try:
            response = requests.get(
                f"{self.interproscan_base_url}/status/{job_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                return response.text.strip()
            else:
                return "ERROR"
                
        except Exception as e:
            print(f"❌ Error checking job status for {job_id}: {e}")
            return "ERROR"
    
    def get_interproscan_results(self, job_id: str) -> Optional[Dict]:
        """
        Retrieve InterProScan results
        
        Args:
            job_id: InterProScan job ID
            
        Returns:
            Results dictionary or None if failed
        """
        try:
            response = requests.get(
                f"{self.interproscan_base_url}/result/{job_id}/json",
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to retrieve results for job {job_id}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error retrieving results for job {job_id}: {e}")
            return None
    
    def wait_for_completion(self, job_id: str, uniprot_id: str, max_wait: int = 3600) -> Optional[Dict]:
        """
        Wait for InterProScan job completion and retrieve results
        
        Args:
            job_id: InterProScan job ID
            uniprot_id: UniProt identifier for logging
            max_wait: Maximum wait time in seconds
            
        Returns:
            Results dictionary or None if failed
        """
        print(f"⏳ Waiting for {uniprot_id} (job {job_id}) to complete...")
        
        start_time = time.time()
        check_interval = 30  # Check every 30 seconds
        
        while time.time() - start_time < max_wait:
            status = self.check_job_status(job_id)
            
            if status == "FINISHED":
                print(f"✅ {uniprot_id} completed successfully!")
                results = self.get_interproscan_results(job_id)
                if results:
                    self.increment_stat('interproscan_completed')
                    return results
                else:
                    self.add_error(f"{uniprot_id}: Failed to retrieve results")
                    return None
                    
            elif status == "ERROR" or status == "FAILURE":
                print(f"❌ {uniprot_id} failed with status: {status}")
                self.add_error(f"{uniprot_id}: Job failed with status {status}")
                return None
                
            elif status == "RUNNING":
                elapsed = int(time.time() - start_time)
                print(f"⏳ {uniprot_id} still running... ({elapsed}s elapsed)")
                time.sleep(check_interval)
                
            else:
                print(f"🔄 {uniprot_id} status: {status}")
                time.sleep(check_interval)
        
        print(f"⏰ {uniprot_id} timed out after {max_wait} seconds")
        self.add_error(f"{uniprot_id}: Timed out after {max_wait} seconds")
        return None
    
    def save_results(self, uniprot_id: str, sequence: str, description: str, results: Dict):
        """
        Save sequence and InterProScan results
        
        Args:
            uniprot_id: UniProt identifier
            sequence: Protein sequence
            description: Protein description
            results: InterProScan results
        """
        try:
            # Save sequence as FASTA
            fasta_path = self.output_dir / "sequences" / f"{uniprot_id}.fasta"
            with open(fasta_path, 'w') as f:
                f.write(f">{description}\n")
                # Write sequence in 80-character lines
                for i in range(0, len(sequence), 80):
                    f.write(sequence[i:i+80] + '\n')
            
            # Save InterProScan results as JSON
            json_path = self.output_dir / "interproscan_results" / f"{uniprot_id}.json"
            with open(json_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"💾 Saved results for {uniprot_id}")
            
        except Exception as e:
            print(f"❌ Error saving results for {uniprot_id}: {e}")
            self.add_error(f"{uniprot_id}: Save error - {str(e)}")
    
    def process_single_protein(self, uniprot_id: str) -> bool:
        """
        Process a single protein through the entire pipeline
        
        Args:
            uniprot_id: UniProt identifier
            
        Returns:
            True if successful, False otherwise
        """
        # Step 1: Fetch sequence
        sequence_data = self.fetch_uniprot_sequence(uniprot_id)
        if not sequence_data:
            self.increment_stat('failed')
            return False
        
        sequence, description = sequence_data
        
        # Step 2: Submit to InterProScan
        job_id = self.submit_to_interproscan(uniprot_id, sequence)
        if not job_id:
            self.increment_stat('failed')
            return False
        
        # Step 3: Wait for completion and get results
        results = self.wait_for_completion(job_id, uniprot_id)
        if not results:
            self.increment_stat('failed')
            return False
        
        # Step 4: Save results
        self.save_results(uniprot_id, sequence, description, results)
        return True
    
    def read_uniprot_ids(self, input_file: str) -> List[str]:
        """Read UniProt IDs from input file"""
        try:
            with open(input_file, 'r') as f:
                ids = [line.strip() for line in f.readlines() if line.strip()]
            print(f"📖 Read {len(ids)} UniProt IDs from {input_file}")
            return ids
        except FileNotFoundError:
            print(f"❌ Input file not found: {input_file}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error reading input file: {e}")
            sys.exit(1)
    
    def process_proteins(self, input_file: str, max_workers: int = 5):
        """
        Process all proteins from input file
        
        Args:
            input_file: Path to input file containing UniProt IDs
            max_workers: Maximum number of concurrent workers
        """
        if not self.email:
            print("❌ Email address is required for InterProScan submissions")
            sys.exit(1)
        
        uniprot_ids = self.read_uniprot_ids(input_file)
        self.stats['total'] = len(uniprot_ids)
        
        print(f"🚀 Starting InterProScan pipeline for {len(uniprot_ids)} proteins...")
        print(f"📁 Output directory: {self.output_dir.absolute()}")
        print(f"📧 Email: {self.email}")
        print(f"👥 Max concurrent jobs: {max_workers}")
        print(f"⚠️  Note: This may take several hours depending on sequence length and server load")
        print("-" * 60)
        
        # Process proteins with limited concurrency
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_id = {
                executor.submit(self.process_single_protein, uniprot_id): uniprot_id
                for uniprot_id in uniprot_ids
            }
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_id):
                uniprot_id = future_to_id[future]
                completed += 1
                
                try:
                    success = future.result()
                    status = "✅ SUCCESS" if success else "❌ FAILED"
                    print(f"[{completed}/{len(uniprot_ids)}] {uniprot_id}: {status}")
                except Exception as e:
                    print(f"[{completed}/{len(uniprot_ids)}] {uniprot_id}: ❌ EXCEPTION - {e}")
                    self.add_error(f"{uniprot_id}: Exception - {str(e)}")
                    self.increment_stat('failed')
        
        self.print_summary()
    
    def print_summary(self):
        """Print processing summary"""
        print("\n" + "=" * 60)
        print("📊 INTERPROSCAN PIPELINE SUMMARY")
        print("=" * 60)
        print(f"Total proteins processed: {self.stats['total']}")
        print(f"Sequences fetched: {self.stats['sequences_fetched']}")
        print(f"InterProScan jobs submitted: {self.stats['interproscan_submitted']}")
        print(f"InterProScan jobs completed: {self.stats['interproscan_completed']}")
        print(f"Failed: {self.stats['failed']}")
        
        if self.stats['total'] > 0:
            success_rate = (self.stats['interproscan_completed'] / self.stats['total']) * 100
            print(f"Success rate: {success_rate:.1f}%")
        
        if self.stats['errors']:
            print(f"\n❌ Errors encountered ({len(self.stats['errors'])}):")
            for error in self.stats['errors'][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more errors")
        
        print(f"\n📁 Results saved in:")
        print(f"  - Sequences: {(self.output_dir / 'sequences').absolute()}")
        print(f"  - InterProScan results: {(self.output_dir / 'interproscan_results').absolute()}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python interproscan_pipeline.py <input_file> <output_directory> <email>")
        print("\nExample:")
        print("  python interproscan_pipeline.py uniprot_ids.txt results/ your_email@example.com")
        print("\nNote: Email is required for InterProScan submissions")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2]
    email = sys.argv[3]
    
    # Validate email format (basic check)
    if '@' not in email or '.' not in email:
        print("❌ Please provide a valid email address")
        sys.exit(1)
    
    # Create pipeline and process proteins
    pipeline = InterProScanPipeline(output_dir, email)
    pipeline.process_proteins(input_file, max_workers=5)

if __name__ == "__main__":
    main()