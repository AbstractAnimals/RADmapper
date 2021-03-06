# -*- coding: utf-8 -*-
'''
Created on 19 March  2012
@author: tcezard
'''
import sys
import os
import re
import logging
from optparse import OptionParser
from glob import glob
import time

from utils import utils_logging, utils_commands
import command_runner
from utils.FastaFormat import FastaReader
from RAD_merge_read1_and_read2 import merge_2_contigs
from RAD_merge_results import merge_by_chunck, concatenate_file


VELVETOPT_ALIAS=["velvetopt","velvetoptimiser"]
VELVET_ALIAS=["velvet"]
VELVETK_ALIAS=["velvetk", "velvetk.pl", "velvetK"]
VELVETKOPT_ALIAS=["velvetkopt", "velvetKopt"]
VELVETKCLC_ALIAS=["velvetkclc"]
CLC_ALIAS=["clc","clcbio"]
SOAPDENOVO_ALIAS=["soap","soapdenovo"]
IDBA_ALIAS=["idba","idba_ud"]
CAP3_ALIAS = ["cap3", "cap"]
NO_ASSEMBLER=["None", "no", ""]



ALL_ASSEMBLERS=[]
ALL_ASSEMBLERS.extend(VELVETOPT_ALIAS)
ALL_ASSEMBLERS.extend(VELVET_ALIAS)
ALL_ASSEMBLERS.extend(VELVETK_ALIAS)
ALL_ASSEMBLERS.extend(VELVETKOPT_ALIAS)
ALL_ASSEMBLERS.extend(VELVETKCLC_ALIAS)
ALL_ASSEMBLERS.extend(CLC_ALIAS)
ALL_ASSEMBLERS.extend(SOAPDENOVO_ALIAS)
ALL_ASSEMBLERS.extend(IDBA_ALIAS)
ALL_ASSEMBLERS.extend(CAP3_ALIAS)
ALL_ASSEMBLERS.extend(NO_ASSEMBLER)

velvetOptimiser_bin="VelvetOptimiser.pl"
velveth_bin="velveth"
velvetg_bin="velvetg"
velvetk_bin="velvetk.pl"
clc_novo_bin = "clc_assembler"
SOAPdenovo_bin="SOAPdenovo31mer"
idba_ud_bin="idba_ud"
cap3_bin = "cap3"


def run_velvetOptimiser(fastq_file_name, low_k=59, high_k=99, outputdir='velvetopt', **kwarg):
    command='rm -rf %s'%outputdir
    if os.path.exists(outputdir):
        return_code = command_runner.run_command(command)
    log_file='%s.log'%outputdir
    command_tmp = "%s -f '-fastq -short %s' --s %s --e %s --k max --c max --d %s 2>&1 >%s"
    command = command_tmp % (velvetOptimiser_bin, fastq_file_name, low_k, high_k, outputdir, log_file)
    return_code = command_runner.run_command(command)
    
    contig_files = glob('%s/contigs.fa'%outputdir)
    # If only one contig file exists, as it should if VelvetOptimiser runs
    # successfully, write out the assembled contig(s)
    contig_file_name=None
    if len(contig_files) == 1:
        contig_file_name = contig_files[0]
    return contig_file_name;


def run_velvet(fastq_file_name, kmer_length=29, output_dir= 'velvet', **kwarg):
    log_file='%s.log'%(output_dir)
    command = "%s %s %s -fastq -short %s 2>&1 >%s"%(velveth_bin, output_dir, kmer_length, fastq_file_name, log_file)
    return_code = command_runner.run_command(command)
    command = "%s %s 2>&1 >%s"%(velvetg_bin, output_dir, log_file)
    return_code = command_runner.run_command(command)

    contig_files = glob('%s/contigs.fa'%output_dir)
    contig_file_name=None
    if len(contig_files) == 1:
        contig_file_name = contig_files[0]
    
    return contig_file_name;


def run_velvetk(fastq_file_name, estimated_size=600, **kwarg):
    command = "%s --size %s --best %s 2> /dev/null"%(velvetk_bin,estimated_size, fastq_file_name)
    logging.info(command)
    stream,process = utils_commands.get_output_stream_from_command(command)
    kmer_length=29
    for line in stream:
        if line.strip().isdigit():
            kmer_length = int(line.strip())
    if kmer_length<19: kmer_length=19
    elif kmer_length>99: kmer_length=99
    logging.info("velvetk kmer: %s"%kmer_length)
    return kmer_length

def run_velvetk_plus_velvet(fastq_file_name, estimated_size=600, **kwarg):
    kmer_length = run_velvetk(fastq_file_name, estimated_size)
    output_dir='velvetk_plus_velvet'
    return run_velvet(fastq_file_name, kmer_length, output_dir)

def run_velvetk_plus_velvetopt(fastq_file_name, estimated_size=600, **kwarg):
    half_range_size=10
    kmer_length = run_velvetk(fastq_file_name, estimated_size)
    output_dir='velvetk_plus_velvetopt'
    if kmer_length-half_range_size<=19: 
        min_k=19
        max_k=39
    elif kmer_length+half_range_size>=99: 
        min_k=79
        max_k=99
    else:
        min_k=kmer_length-half_range_size
        max_k=kmer_length+half_range_size
    logging.info("velvetk kmer range: %s-%s"%(min_k,max_k))
    return run_velvetOptimiser(fastq_file_name, min_k, max_k, output_dir)


def run_velvetk_plus_clc(fastq_file_name, estimated_size=600, **kwarg):
    kmer_length = run_velvetk(fastq_file_name, estimated_size)
    if kmer_length<12: kmer_length=12
    elif kmer_length>64: kmer_length=64
    output_dir='velvetk_plus_clc'
    return run_clc_assemble(fastq_file_name, kmer_length, output_dir)


def run_clc_assemble(fastq_file_name, word_size=None, output_dir='clc_bio', **kwarg):
    log_file='%s.log'%output_dir
    command='mkdir %s'%output_dir
    if not os.path.exists(output_dir):
        return_code = command_runner.run_command(command)
    if word_size:
        command = "%s -v -w %s -q %s -o clc_bio/contigs.fa -b 200 -m 100 2>&1 >%s " % (
        clc_novo_bin, word_size, fastq_file_name, log_file)
    else:
        command = "%s -v -q %s -o clc_bio/contigs.fa -b 200 -m 100 2>&1 >%s " % (
        clc_novo_bin, fastq_file_name, log_file)
    return_code = command_runner.run_command(command)
    contig_files = glob('%s/contigs.fa'%output_dir)
    contig_file_name=None
    if len(contig_files) == 1:
        contig_file_name = contig_files[0]
    return contig_file_name;


def run_soapdenovo(fastq_file_name, max_read_len=101, **kwarg):
    log_file='soapdenovo.log'
    command='mkdir soapdenovo'
    if not os.path.exists('soapdenovo'):
        return_code = command_runner.run_command(command)
    config_file='soapdenovo/config_file'
    open_file=open(config_file,'w')
    open_file.write("max_rd_len=%s\n[LIB]\nq=%s\n"%(max_read_len,fastq_file_name))
    open_file.close()
    command='%s pregraph -K 29 -s %s -o soapdenovo/graph -p 1 2>&1 >%s'%(SOAPdenovo_bin, config_file,log_file)
    return_code = command_runner.run_command(command)
    command='%s contig -g soapdenovo/graph 2>&1 >>%s'%(SOAPdenovo_bin,log_file)
    return_code = command_runner.run_command(command)
    contig_files = glob('soapdenovo/graph.contig')
    contig_file_name=None
    if len(contig_files) == 1:
        contig_file_name = contig_files[0]
    return contig_file_name


def run_idba(fastq_file_name, max_read_len=200, **kwarg):
    log_file='idba_ud.log'
    command="%s -r %s -o idba_ud --min_contig %s --num_threads 1 --mink 40  --min_count 8 --min_support 4   2>&1 >%s"%(idba_ud_bin,fastq_file_name, max_read_len,log_file)
    return_code = command_runner.run_command(command)
    contig_files = glob('idba_ud/contig.fa')
    contig_file_name=None
    if len(contig_files) == 1:
        contig_file_name = contig_files[0]
    return contig_file_name


def run_cap3(fastq_file_name, output_dir="cap3", **kwarg):
    log_file = '%s.log' % output_dir
    fasta_file = os.path.join(output_dir, os.path.basename(fastq_file_name) + '.fa')
    command = 'mkdir %s' % output_dir
    if not os.path.exists(output_dir):
        return_code = command_runner.run_command(command)
    command = "seqtk seq -A %s > %s" % (fastq_file_name, fasta_file)
    return_code = command_runner.run_command(command)

    command = "%s %s 2>&1 >%s" % (cap3_bin, fasta_file, log_file)
    return_code = command_runner.run_command(command)
    contig_files = glob('%s.cap.contigs' % (fasta_file))
    contig_file_name = None
    if len(contig_files) == 1:
        contig_file_name = contig_files[0]
    return contig_file_name


def pass_function(*args, **kwarg):
    pass

def correct_contig_file(contig_file, site_name, min_contig_len=101):
    dir_name=os.path.dirname(contig_file)
    corrected_file=os.path.join(dir_name,'contigs_corrected.fa')
    open_file = open(contig_file)
    open_corrected=open(corrected_file,'w')
    fasta_reader = FastaReader(open_file)
    nb_seq=0
    max_len=0
    for fasta_record in fasta_reader:
        header, sequence=fasta_record
        length_A = sum([len(e) for e in re.findall('[A]{7,}', sequence)])
        length_C = sum([len(e) for e in re.findall('[C]{7,}', sequence)])
        length_G = sum([len(e) for e in re.findall('[G]{7,}', sequence)])
        length_T = sum([len(e) for e in re.findall('[T]{7,}', sequence)])
        total_repeat = sum([length_A, length_C, length_G, length_T])

        if len(sequence) > min_contig_len and float(total_repeat) / len(sequence) < .5:
            nb_seq+=1
            if len(sequence)>max_len:
                max_len=len(sequence)
            header='%s_pair_%s_length_%s'%(site_name,nb_seq,len(sequence))
            open_corrected.write('>%s\n%s\n'%(header,sequence))
    open_corrected.close()
    open_file.close()
    return (corrected_file, nb_seq, max_len)


def clean_fastq(fastq_file, adapter_file=None, rg_ids=[], subsample_nb_read=None):
    if rg_ids:
        fastq_file = keep_read_from_samples(fastq_file, rg_ids)
    if adapter_file:
        adapter_trim = fastq_file + '.adapter_trimmed'
        if not os.path.exists(adapter_trim):
            command = "scythe -q sanger -a %s -o %s %s" % (adapter_file, adapter_trim, fastq_file)
            command_runner.run_command(command)
        fastq_file = adapter_trim
    qual_trim = fastq_file + ".qual_trimmed"
    if not os.path.exists(qual_trim):
        command = "sickle se -f %s -t sanger -o %s" % (fastq_file, qual_trim)
        command_runner.run_command(command)
        fastq_file = qual_trim
    if subsample_nb_read:
        sub_sampled = qual_trim + ".%s" % subsample_nb_read
        if not os.path.exists(sub_sampled):
            command = "seqtk sample %s %s > %s" % (fastq_file, subsample_nb_read, sub_sampled)
            command_runner.run_command(command)
        return sub_sampled
    else:
        return fastq_file


def keep_read_from_samples(fastq_file, rg_ids=[]):
    filtered = fastq_file + '.RG_filtered'
    logging.info('Remove unwanted Read groups from %s > %s' % (fastq_file, filtered))
    fastq_to_keep = []
    fastq_lines = []
    line_count = 0
    with open(fastq_file, 'r') as open_input:
        for line in open_input:
            line_count += 1
            fastq_lines.append(line.strip())
            if line_count % 4 == 0:
                rg = fastq_lines[0].split('RGID:')[1].strip('/2')
                if rg in rg_ids:
                    fastq_to_keep.append('\n'.join(fastq_lines))
                fastq_lines = []

    with open(filtered, 'w') as open_output:
        open_output.write('\n'.join(fastq_to_keep))
    return filtered


def run_assembly(assembly_function, fastq_file, output_dir=None, estimated_size=600, subsample_nb_read=None, rg_ids=[], name=None,
                 adapter_file=None):
    if name is None:
        name,ext =os.path.splitext(os.path.basename(fastq_file))
    current_dir=None
    if output_dir and os.path.exists(output_dir):
        logging.debug('change directory to %s'%output_dir)
        current_dir=os.getcwd()
        os.chdir(output_dir)
    fastq_file = clean_fastq(fastq_file, adapter_file=adapter_file, rg_ids=rg_ids, subsample_nb_read=subsample_nb_read)
    contig_file = assembly_function(fastq_file, estimated_size=estimated_size)
    if contig_file:
        contig_file = os.path.abspath(contig_file)
        merged_consensus = os.path.join(os.path.dirname(contig_file),'merged_consensus.fa')
        if os.path.exists(merged_consensus):
            logging.debug('remove the merged_consensus.fa that already exists before assembling')
            command = 'rm -f %s'%(merged_consensus)
            command_runner.run_command(command)

    if current_dir:
        logging.debug('change directory back to %s'%current_dir)
        os.chdir(current_dir)
    nb_seq=max_len=0
    corrected_contig_file=None
    if contig_file:
        corrected_contig_file, nb_seq, max_len = correct_contig_file(contig_file, name)
    return (corrected_contig_file,nb_seq, max_len)

def get_best_assembly(assembly_dir):
    contigs_file_to_compare = glob(os.path.join(assembly_dir,"*/contigs_corrected.fa"))
    contigs_file_to_compare.sort(cmp=compare_contig_file)
    return contigs_file_to_compare[0]

def get_best_assembly_merged(assembly_dir, read1_fasta, name, force_merge=False):
    contigs_file_to_compare = glob(os.path.join(assembly_dir,"*/contigs_corrected.fa"))
    if len(contigs_file_to_compare)==0:
        return 'None', read1_fasta

    contigs_file_to_compare.sort(cmp=compare_contig_file)

    best_assembly=None
    for contig_file2 in contigs_file_to_compare:
        output_dir=os.path.dirname(contig_file2)
        merged_contig_file = merge_read1_and_read2_contigs(name, read1_fasta, contig_file2, output_dir)
        print merged_contig_file
        if merged_contig_file:
            best_assembly=merged_contig_file
            name=os.path.basename(os.path.dirname(contig_file2))
            logging.info("Best assembly with %s: Merged"%name)
            break
    
    if best_assembly is None :
        name=os.path.basename(os.path.dirname(contigs_file_to_compare[0]))
        best_assembly=os.path.join(assembly_dir,name,"merged_consensus.fa")
        if force_merge:
            logging.info("Best assembly with %s: Force merge"%name)
            force_merge_consensus(read1_fasta, contigs_file_to_compare[0], best_assembly)
        else:
            logging.info("Best assembly with %s: Concatenated"%name)
            concatenate_consensus([read1_fasta, contigs_file_to_compare[0]], best_assembly)
    return name,best_assembly


def compare_fasta_length(fasta_rec1,fasta_rec2):
    h1, s1 = fasta_rec1
    h2, s2 = fasta_rec2
    return len(s2)-len(s1)

def merge_read1_and_read2_contigs(name, read1_contig, read2_contigs, output_dir):
    open_read2=open(read2_contigs)
    all_fasta2_entries=[]
    read2_reader = FastaReader(open_read2)
    for header, sequence in read2_reader:
        all_fasta2_entries.append((header,sequence))
    if len(all_fasta2_entries)==1:
        merged_contigs_info = merge_2_contigs(name, read1_contig, read2_contigs, output_dir)
        if merged_contigs_info:
            merged_contig_file=os.path.join(output_dir,'tmp_merged_consensus.fa')
            with open(merged_contig_file,'w') as open_output:
                open_output.write('>%s\n%s\n'%merged_contigs_info)
            return merged_contig_file
        else:
            return None
    else:
        all_fasta2_entries.sort(cmp=compare_fasta_length)
        merged_pair = None
        remaining=[]
        for header,sequence in all_fasta2_entries:
            cur_pair=os.path.join(output_dir,header+".fa")
            open_pair = open(cur_pair,'w')
            open_pair.write(">%s\n%s\n"%(header,sequence))
            open_pair.close()
            if not merged_pair: 
                merged_pair = merge_2_contigs(name, read1_contig, cur_pair, output_dir)
                if not merged_pair:
                    remaining.append(cur_pair)
            else:
                results = merge_2_contigs(name+"add", read1_contig, cur_pair, output_dir)
                #TODO: fix this as it doesn't seems to trim and the output file is the same as above but in the mean time disable using False
                if False and results:
                    additional_merged_pair=os.path.join(output_dir,'tmp_merged_consensus.fa')
                    with open(additional_merged_pair,'w') as open_output:
                        open_output.write('>%s\n%s\n'%results)

                    #trim this contig
                    trim_additional_merged_contigs(cur_pair, additional_merged_pair)
                remaining.append(cur_pair)
            
        merge_file = os.path.join(output_dir,"merged_consensus.fa")
        if merged_pair:
            merged_pair_file=os.path.join(output_dir,'tmp_merged_consensus.fa')
            with open(merged_pair_file,'w') as open_output:
                open_output.write('>%s\n%s\n'%merged_pair)
            tmp = [merged_pair_file]
            tmp.extend(remaining)
            concatenate_consensus(tmp,merge_file)
            return merge_file
        else:
            return None

def trim_additional_merged_contigs(original_contig, merged_contig):
    open_merged=open(merged_contig)
    fasta_reader=FastaReader(open_merged)
    header, sequence = fasta_reader.next()
    sp_header = header.split('_')
    trim=int(sp_header[-2].strip('os'))
    cigar=sp_header[-1]
    all_cigar = re.findall('(\d+)([MXDI])', cigar)
    for count, type  in all_cigar:
        if type=="M" or type=="X":
            trim+=int(count)
    
    open_merged.close()
    if trim>50:
        logging.info("trim %s of %s"%(trim, original_contig))
        open_contig=open(original_contig)
        fasta_reader=FastaReader(open_contig)
        header, sequence,fasta_reader.next()
        header=header+"trim_%s"%trim
        sequence=sequence[trim:]
        open_contig.close()
        open_contig=open(original_contig, 'w')
        if len(sequence)>100:
            open_contig.write(">%s\n%s\n"%(header,sequence))
        open_contig.close()
    

def concatenate_consensus(all_fasta_files,output_merge_file):
    output_file = merge_by_chunck(all_fasta_files, concatenate_file, output_merge_file,
                                  output_dir=os.path.dirname(output_merge_file))
    #command = "cat %s > %s "%(' '.join(all_fasta_files), output_merge_file)
    #command_runner.run_command(command)


def force_merge_consensus(read1_consensus, read2_consensus, output_merge_file):
    open_output = open(output_merge_file,'w')
    open_read1 = open(read1_consensus)
    open_read2 = open(read2_consensus)
    fasta_reader1 = FastaReader(open_read1)
    read1_name, read1_sequence = fasta_reader1.next()
    open_read1.close()
    name="%s_forced_merged"%read1_name
    array=[read1_sequence]
    fasta_reader2 = FastaReader(open_read2)
    for read2_name, read2_sequence in fasta_reader2:
        name="%s_%s"%(name,read2_name)
        array.append("N"*100)
        array.append(read2_sequence)
    

    open_output.write(">%s\n%s\n"%(name, ''.join(array)))
    open_read2.close()
    open_output.close()


def get_list_of_length(contig_file):
    open_file = open(contig_file)
    list_length=[]
    nb_contig=0
    max_length=0
    fasta_reader = FastaReader(open_file)
    for fasta_record in fasta_reader:
        header, sequence=fasta_record
        nb_contig+=1
        if len(sequence)>max_length: max_length=len(sequence)
    return nb_contig, max_length


def compare_contig_file(contig_file1,contig_file2):
    nb_contig1, max_length1 = get_list_of_length(contig_file1)
    nb_contig2, max_length2 = get_list_of_length(contig_file2)
    if nb_contig1==nb_contig2:
        return max_length2-max_length1
    else:
        return nb_contig1-nb_contig2


def run_one_fastq_file(fastq_file, output_dir, assembly_function_list, estimated_size=600, subsample_nb_read=None, rg_ids=[],
                       read1_fasta=None, name=None, force_merge=False, adapter_file=None):
    fastq_file=os.path.abspath(fastq_file)
    #output_dir='%s_dir'%fastq_file
    if not os.path.exists(output_dir):
        command='mkdir %s'%(output_dir)
        return_code = command_runner.run_command(command)
    for assembly_function in assembly_function_list:
        #Assemble with provided assembler
        (contig_file, nb_seq, max_len) = run_assembly(assembly_function, fastq_file, output_dir,
                                                      estimated_size=estimated_size,
                                                      subsample_nb_read=subsample_nb_read, rg_ids=rg_ids,
                                                      name=name, adapter_file=adapter_file)
        #Merge read one and read2 contig
        if contig_file:
            #TODO: This function gets run twice need to change that as the second run is not useful
            merge_read1_and_read2_contigs(name, read1_contig=read1_fasta, read2_contigs=contig_file, output_dir=os.path.dirname(contig_file))
        
    best_assembler_name, best_assembly_file = get_best_assembly_merged(output_dir, read1_fasta, name, force_merge)

    command="cp %s %s"%(best_assembly_file, os.path.join(output_dir, "best_assembly.fa"))
    return_code = command_runner.run_command(command)
    return os.path.join(output_dir, "best_assembly.fa")


def run_all_fastq_files(directory, assembly_function_list, estimated_size, subsample_nb_read=None, rg_ids=[], force_merge=False,
                        adapter_file=None):
    directory=os.path.abspath(directory)
    all_consensus_dirs = glob(os.path.join(directory,'*_dir'))

    all_contig_list=[]
    for output_dir in all_consensus_dirs:
        name=os.path.basename(output_dir)[:-len("_dir")]
        fastq_file=os.path.join(output_dir,name+"_2.fastq")
        read1_fasta=os.path.join(output_dir,name+"_1.fa")
        contig_file = run_one_fastq_file(fastq_file, output_dir, assembly_function_list, estimated_size=estimated_size,
                                         subsample_nb_read=subsample_nb_read, rg_ids=rg_ids, read1_fasta=read1_fasta,
                                         name=name, force_merge=force_merge, adapter_file=adapter_file)
        if contig_file:
            all_contig_list.append(contig_file)
        logging.info("\n")


def get_assembly_function(assembler_name):
    if assembler_name in VELVETOPT_ALIAS:
        return run_velvetOptimiser
    if assembler_name in VELVET_ALIAS:
        return run_velvet
    if assembler_name in VELVETK_ALIAS:
        return run_velvetk_plus_velvet
    if assembler_name in VELVETKOPT_ALIAS:
        return run_velvetk_plus_velvetopt
    if assembler_name in VELVETKCLC_ALIAS:
        return run_velvetk_plus_clc
    if assembler_name in CLC_ALIAS:
        return run_clc_assemble
    if assembler_name in SOAPDENOVO_ALIAS:
        return run_soapdenovo
    if assembler_name in IDBA_ALIAS:
        return run_idba
    if assembler_name in CAP3_ALIAS:
        return run_cap3
    if assembler_name in NO_ASSEMBLER:
        return pass_function
    logging.error("Unknown assembler: %s"%assembler_name)
    return None

    
def main():
    #initialize the logging
    utils_logging.init_logging(logging.INFO)
    #utils_logging.init_logging(logging.CRITICAL)
    #Setup options
    optparser=_prepare_optparser()
    (options,args) = optparser.parse_args()
    #verify options
    arg_pass=_verifyOption(options)
    if not arg_pass:
        logging.warning(optparser.get_usage())
        logging.critical("Non valid arguments: exit")
        sys.exit(1)
    if options.debug:
        utils_logging.init_logging(logging.DEBUG)
    if not options.print_command:
        command_runner.set_command_to_run_localy()
    start_time = time.time()
    #comment = '%s: contig_align:%s, mismatches:%s site with 1 contig:%s site with more than 1 contig:%s'
    all_assembler_to_try = options.assembler_name.split(',')
    assembly_function_list=[]
    for assembler_name in all_assembler_to_try:
        assembly_function=get_assembly_function(assembler_name)
        assembly_function_list.append(assembly_function)
    if options.rg_ids:
        rg_ids=options.rg_ids.split()
    else:
        rg_ids=[]
    if options.fastq_dir:
        run_all_fastq_files(options.fastq_dir, assembly_function_list, options.estimated_size,
                            options.subsample_nb_read, rg_ids,
                            options.force_merge, adapter_file=options.adapter_file)
    elif options.fastq_file:
        output_dir = os.path.dirname(options.fastq_file)
        name = os.path.basename(options.fastq_file)[:-len("_2.fastq")]
        read1_fasta = os.path.join(output_dir, name + "_1.fa")
        contig_file = run_one_fastq_file(options.fastq_file, output_dir, assembly_function_list,
                                         estimated_size=options.estimated_size,
                                         subsample_nb_read=options.subsample_nb_read,
                                         read1_fasta=read1_fasta, name=name, force_merge=options.force_merge,
                                         adapter_file=options.adapter_file)
    logging.info("Elapsed time:%.1f seconds"%(time.time()-start_time))

def _prepare_optparser():
    """Prepare optparser object. New options will be added in this
    function first.
    """
    usage = """usage: %prog <-b bam_file> [ -o output_file]"""
    description = """This script will take aligned RAD read to the consensuses and calculate per consensus coverage."""
    
    optparser = OptionParser(version="None",description=description,usage=usage,add_help_option=False)
    optparser.add_option("-h","--help",action="help",help="show this help message and exit.")
    optparser.add_option("-f","--fastq_file",dest="fastq_file",type="string",
                         help="Path to one fastq_file. Default: %default")
    optparser.add_option("-d","--fastq_dir",dest="fastq_dir",type="string",
                         help="Path to a directory containing fastq file (only extension .fastq will be processed). Default: %default")
    optparser.add_option("-a","--assembler_name",dest="assembler_name",type="string",default=None,
                         help="The name of the assembler that will be used on the fastq files. Default: %default")
    optparser.add_option("-s","--estimated_size",dest="estimated_size",type="string",default="600",
                         help="The estimated size of the contig to assemble. It is used by velvetk to estimate the best kmer. Default: %default")
    optparser.add_option("-S", "--subsample_nb_read", dest="subsample_nb_read", type="int", default=0,
                         help="sub sample to the specified number of read before assembly. Default: %default")
    optparser.add_option("-A", "--adapter_file", dest="adapter_file", type="string",
                         default="/ifs/seqarchive/adapters/illumina_adapters_20150126.fasta",
                         help="Specify an adapter file to trim before running the assembly. Default: %default")
    optparser.add_option("--rg_ids", dest="rg_ids", type="string", default="",
                         help="Specify a list of read group ids that will be used for the assembly. Default: %default")
    optparser.add_option("--force_merge",dest="force_merge",action='store_true',default=False,
                         help="Force merged the consensus: add a run of 100 N in between each sequence. Default: %default")
    optparser.add_option("--print",dest="print_command",action='store_true',default=False,
                         help="print the commands instead of running them. Default: %default")
    optparser.add_option("--debug",dest="debug",action='store_true',default=False,
                         help="Output debug statment. Default: %default")
    return optparser


def _verifyOption(options):
    """Check if the mandatory option are present in the options objects.
    @return False if any argument is wrong."""
    arg_pass=True
    
    return arg_pass



if __name__=="__main__":
    main()
    
