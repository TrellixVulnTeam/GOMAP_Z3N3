import logging, os, re, json, sys
from code.utils.basic_utils import check_output_and_run
from code.utils.split_fa import split_fasta
from code.utils.blast_utils import combine_blast_xml
from glob import glob
from pprint import pprint
from distutils.version import StrictVersion

def process_fasta(config):
    workdir=config["input"]["gomap_dir"]+"/"
    fa_file=workdir + "input/" + config["input"]["fasta"]
    split_dir=workdir + config["data"]["mixed-method"]["preprocess"]["fa_path"]
    num_seqs=config["data"]["mixed-method"]["preprocess"]["num_seqs"]
    split_fasta(fa_file,split_dir,num_seqs)

def make_uniprotdb(config):
    uniprot_fa = config["mixed-method"]["preprocess"]["uniprot_db"]+".fa"
    uniprot_db = config["mixed-method"]["preprocess"]["uniprot_db"]
    uniprot_db_dir = os.path.dirname(uniprot_db)

    db_dir = os.path.dirname(uniprot_db)   
    files = os.listdir("mixed-method/data/blastdb/")
    db_pattern = os.path.basename(uniprot_db)
    db_pattern = re.compile(db_pattern+".*phd")

    db_exist = [(1 if db_pattern.match(tmp_file) is not None else 0) for tmp_file in files]
    makedb_cmd= ["makeblastdb", "-in", uniprot_fa, "-dbtype", "prot", "-out", uniprot_db, "-parse_seqids", "-hash_index","-max_file_sz","10GB"]
    if 1 in db_exist:
        logging.warn("The Uniprot blast database already exists, if not remove the database files to recreate the database")
        logging.info(makedb_cmd)
    else:
        check_output_and_run("temp/uniprotdb",makedb_cmd)

def make_tmp_fa(config):
    workdir=config["input"]["gomap_dir"]+"/"
    fa_path=workdir + config["data"]["mixed-method"]["preprocess"]["fa_path"]
    tmp_fa_dir=workdir + config["data"]["mixed-method"]["preprocess"]["blast_out"]+"/temp/"
    small_seqs=config["data"]["mixed-method"]["preprocess"]["small_seqs"]
    fa_pattern=fa_path+"/"+config["input"]["basename"]+"*.fa"
    fa_files = glob(fa_pattern)
    
    for fa_file in fa_files:
        split_fasta(fa_file,tmp_fa_dir,small_seqs)

def run_uniprot_blast(config):
    workdir=config["input"]["gomap_dir"]+"/"
    tmp_fa_dir=workdir + config["data"]["mixed-method"]["preprocess"]["blast_out"]+"/temp"
    fa_pattern=tmp_fa_dir+"/"+config["input"]["basename"]+"*.fa"
    fa_files = sorted(glob(fa_pattern))

    if config["input"]["mpi"] is True:
        from code.utils.run_mpi_blast import run_mpi_blast
        run_mpi_blast(fa_files,config)
    else:
        from code.utils.run_single_blast import run_single_blast
        run_single_blast(fa_files,config)



def compile_blast_out(config):
    workdir=config["input"]["gomap_dir"]+"/"
    tmp_fa_dir=workdir + config["data"]["mixed-method"]["preprocess"]["fa_path"]
    fa_pattern=tmp_fa_dir+"/"+config["input"]["basename"]+"*.fa"
    tmp_bl_dir=workdir + config["data"]["mixed-method"]["preprocess"]["blast_out"]+"/temp"

    fa_files = sorted(glob(fa_pattern))
    for fa_file in fa_files:        
        tmp_fa_pat=re.sub(r'.fa$',"",os.path.basename(fa_file))
        tmp_bl_out=workdir + config["data"]["mixed-method"]["preprocess"]["blast_out"]+"/"+tmp_fa_pat+".xml"
        bl_pattern=tmp_bl_dir+"/"+tmp_fa_pat+"*.xml"
        all_tmp_bl_files = sorted(glob(bl_pattern))
        combine_blast_xml(all_tmp_bl_files,tmp_bl_out)