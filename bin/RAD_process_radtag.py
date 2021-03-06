#!/usr/bin/env python
'''
Created on 21 Jan 2010

@author: tcezard
'''
#!/usr/bin/env python
import sys, logging
from optparse import OptionParser
import re
from utils.Binning import Distribution_holder
from utils.utils_commands import get_output_stream_from_command
from utils import utils_logging
import os
from wiki_communication import get_wiki_project

barcode_to_old_id={'TAGCA':'C02',
                'GTACA':'A11',
                'TGACC':'C05',
                'TAATG':'C01',
                'TCGAG':'C04',
                'CGGCG':'A02',
                'CGATA':'A01',
                'CTAGG':'A03',
                'CTGAA':'A04',
                'AGAGT':'E05',
                'GCGCC':'A08',
                'GTGTG':'A12',
                'GCATT':'A07',
                'GAGAT':'A06'}


dummy={'TAGCA':'RD-P1-013-C02',
                'GTACA':'RD-P1-060-A11',
                'TGACC':'RD-P1-031-C05',
                'TAATG':'RD-P1-061-C01',
                'TCGAG':'RD-P1-030-C04',
                'CGGCG':'RD-P1-040-A02',
                'CGATA':'RD-P1-005-A01',
                'CTAGG':'RD-P1-006-A03',
                'CTGAA':'RD-P1-007-A04',
                'AGAGT':'RD-P1-020-E05',
                'GCGCC':'RD-P1-026-A08',
                'GTGTG':'RD-P1-059-A12',
                'GCATT':'RD-P1-043-A07',
                'GAGAT':'RD-P1-057-A06'}


barcode_lookup_modified={'CAGTC':'RD-P1-039',
                'CCCCA':'RD-P1-038',
                'TTTTA':'RD-P1-032',
                'ATTAG':'RD-P1-019',
                'ACGTA':'RD-P1-018',
                'AACCC':'RD-P1-017',
                'TTAAT':'RD-P1-016',
                'TGTGG':'RD-P1-015',
                'TCCTC':'RD-P1-014',
                'TAGCA':'RD-P1-013-C02',
                'GTCAC':'RD-P1-012',
                'GGCCT':'RD-P1-011',
                'GCTAA':'RD-P1-010',
                'TACGT':'RD-P1-029',
                'TCTCT':'RD-P1-062',
                'TGCAA':'RD-P1-063',
                'ATCGA':'RD-P1-035',
                'GTACA':'RD-P1-060-A11',
                'TGACC':'RD-P1-031-C05',
                'TAATG':'RD-P1-061-C01',
                'TCGAG':'RD-P1-030-C04',
                'CGTAT':'RD-P1-022',
                'TTCCG':'RD-P1-048',
                'AATTT':'RD-P1-049',
                'CTCTT':'RD-P1-023',
                'GGTTC':'RD-P1-044',
                'TATAC':'RD-P1-045',
                'TCAGA':'RD-P1-046',
                'TGGTT':'RD-P1-047',
                'CGGCG':'RD-P1-040-A02',
                'AAGGG':'RD-P1-033',
                'GGGGA':'RD-P1-042',
                'GTTGT':'RD-P1-028',
                'XXXXX':'RD-P1-000',
                'AAAAA':'RD-P1-001',
                'ACCAT':'RD-P1-002',
                'AGGAC':'RD-P1-003',
                'ATATC':'RD-P1-004',
                'CGATA':'RD-P1-005-A01',
                'CTAGG':'RD-P1-006-A03',
                'CTGAA':'RD-P1-007-A04',
                'CGCGC':'RD-P1-008',
                'GAAGC':'RD-P1-009',
                'AGAGT':'RD-P1-020-E05',
                'CCAAC':'RD-P1-021',
                'GCGCC':'RD-P1-026-A08',
                'GGAAG':'RD-P1-027',
                'CCTTG':'RD-P1-024',
                'GACTA':'RD-P1-025',
                'TTGGC':'RD-P1-064',
                'CAACT':'RD-P1-037',
                'ACACG':'RD-P1-036',
                'ACTGC':'RD-P1-034',
                'ATGCT':'RD-P1-050',
                'GATCG':'RD-P1-041',
                'GTGTG':'RD-P1-059-A12',
                'GCCGG':'RD-P1-058',
                'CTTCC':'RD-P1-053',
                'AGTCA':'RD-P1-052',
                'AGCTG':'RD-P1-051',
                'GCATT':'RD-P1-043-A07',
                'GAGAT':'RD-P1-057-A06',
                'CACAG':'RD-P1-056',
                'CCGGT':'RD-P1-055',
                'CATGA':'RD-P1-054',
                'AGTAC':'wrong_A11',
                'ATAAT':'wrong_C01',
                'ACGAT':'wrong_A01',
                'ACTAG':'wrong_A03',
                'ACTGA':'wrong_A04',
                'AGTGT':'wrong_A12',
                'ATAGC':'wrong_C02',
                'AAGAG':'wrong_E05',
                'AGCGC':'wrong_A08',
                #'ATCGA':'wrong_C04',
                'ATGAC':'wrong_C05',
                'ACGGC':'wrong_A02',
                'AGCAT':'wrong_A07',
                'AGAGA':'wrong_A06'}

barcode_lookup={'CAGTC':'RD-P1-039',
                'CCCCA':'RD-P1-038',
                'TTTTA':'RD-P1-032',
                'ATTAG':'RD-P1-019',
                'ACGTA':'RD-P1-018',
                'AACCC':'RD-P1-017',
                'TTAAT':'RD-P1-016',
                'TGTGG':'RD-P1-015',
                'TCCTC':'RD-P1-014',
                'TAGCA':'RD-P1-013',
                'GTCAC':'RD-P1-012',
                'GGCCT':'RD-P1-011',
                'GCTAA':'RD-P1-010',
                'TACGT':'RD-P1-029',
                'TCTCT':'RD-P1-062',
                'TGCAA':'RD-P1-063',
                'ATCGA':'RD-P1-035',
                'GTACA':'RD-P1-060',
                'TGACC':'RD-P1-031',
                'TAATG':'RD-P1-061',
                'TCGAG':'RD-P1-030',
                'CGTAT':'RD-P1-022',
                'TTCCG':'RD-P1-048',
                'AATTT':'RD-P1-049',
                'CTCTT':'RD-P1-023',
                'GGTTC':'RD-P1-044',
                'TATAC':'RD-P1-045',
                'TCAGA':'RD-P1-046',
                'TGGTT':'RD-P1-047',
                'CGGCG':'RD-P1-040',
                'AAGGG':'RD-P1-033',
                'GGGGA':'RD-P1-042',
                'GTTGT':'RD-P1-028',
                'XXXXX':'RD-P1-000',
                'AAAAA':'RD-P1-001',
                'ACCAT':'RD-P1-002',
                'AGGAC':'RD-P1-003',
                'ATATC':'RD-P1-004',
                'CGATA':'RD-P1-005',
                'CTAGG':'RD-P1-006',
                'CTGAA':'RD-P1-007',
                'CGCGC':'RD-P1-008',
                'GAAGC':'RD-P1-009',
                'AGAGT':'RD-P1-020',
                'CCAAC':'RD-P1-021',
                'GCGCC':'RD-P1-026',
                'GGAAG':'RD-P1-027',
                'CCTTG':'RD-P1-024',
                'GACTA':'RD-P1-025',
                'TTGGC':'RD-P1-064',
                'CAACT':'RD-P1-037',
                'ACACG':'RD-P1-036',
                'ACTGC':'RD-P1-034',
                'ATGCT':'RD-P1-050',
                'GATCG':'RD-P1-041',
                'GTGTG':'RD-P1-059',
                'GCCGG':'RD-P1-058',
                'CTTCC':'RD-P1-053',
                'AGTCA':'RD-P1-052',
                'AGCTG':'RD-P1-051',
                'GCATT':'RD-P1-043',
                'GAGAT':'RD-P1-057',
                'CACAG':'RD-P1-056',
                'CCGGT':'RD-P1-055',
                'CATGA':'RD-P1-054'}

def parse_process_radtag(process_radtag,pools_file, project_id=None):
    all_barcode_2_sample = read_pools_file(pools_file)
    open_file = open(process_radtag)
    section=0
    for line in open_file:
        if line.strip()=='':
            section+=1
            print ''
            continue
        if section==0:
            if line.startswith('Total Sequences'):
                total_sequence=int(line.strip().split()[2])
            print line.strip()
        elif section==1:
            if line.startswith('Barcode'):
                barcode, total, no_radtag, retained = line.strip().split('\t')
                out=[barcode, 'Barcode ID','Sample ID', "External ID", total, '%%%s'%(total), no_radtag,'%%%s'%(no_radtag), retained, '%%%s'%(retained)]
                print '\t'.join(out)
            else:
                barcode, total, no_radtag, retained = line.strip().split()
                modified_barcode = barcode_lookup_modified.get(barcode,'')
                sample_id = all_barcode_2_sample.get(barcode,'')
                external_id=''
                if project_id is not None and sample_id:
                    project = get_wiki_project(project_id)
                    sample = project.get_sample(sample_id)
                    if sample:
                        external_id = sample.get_external_id()
                out=[barcode, modified_barcode, sample_id, external_id, total]
                
                out.append('%.2f%%'%(float(total)*100/total_sequence))
                out.append(no_radtag)
                out.append('%.2f%%'%(float(no_radtag)/float(total)*100))
                out.append(retained)
                out.append('%.2f%%'%(float(retained)/float(total)*100))
                print '\t'.join(out)
        elif section==2:
            if line.startswith('Barcode') or line.startswith('Sequences'):
                if line.startswith('Barcode'):
                    barcode, total = line.strip().split('\t')
                    out=[barcode, 'Barcode ID', total, '%%%s'%(total)]
                    print '\t'.join(out)
                else:
                    print line.strip()
            else:
                barcode, total = line.strip().split()
                out=[barcode, str(barcode_lookup.get(barcode,'')), total]
                out.append('%.2f%%'%(float(total)*100/total_sequence))
                print '\t'.join(out)
                
def parse_process_radtag_for_wiki(process_radtag,pools_file):
    all_barcode_2_sample = read_pools_file(pools_file)
    open_file = open(process_radtag)
    section=0
    for line in open_file:
        if line.strip()=='':
            section+=1
            print ''
            continue
        if section==0:
            if line.startswith('Total Sequences'):
                total_sequence=int(line.strip().split()[2])
        elif section==1:
            if line.startswith('Barcode'):
                barcode, total, no_radtag, retained = line.strip().split('\t')
                out=[barcode, 'Barcode ID','Sample ID', total, '%%%s'%(total), no_radtag,'%%%s'%(no_radtag), retained, '%%%s'%(retained)]
                print '||%s||'%'||'.join(out)
            else:
                barcode, total, no_radtag, retained = line.strip().split()
                
                out=[barcode, barcode_lookup_modified.get(barcode,' '), all_barcode_2_sample.get(barcode,''), total]
                out.append('%.2f%%'%(float(total)*100/total_sequence))
                out.append(no_radtag)
                out.append('%.2f%%'%(float(no_radtag)/float(total)*100))
                out.append(retained)
                out.append('%.2f%%'%(float(retained)/float(total)*100))
                print '|%s|'%'|'.join(out)
        elif section==2:
            pass



def read_pools_file(pools_file):
    if not pools_file:
        return {}
    open_pools = open(pools_file)
    all_barcodes_2_samples={}
    for line in open_pools:
        sp_line=line.strip().split()
        if len(sp_line)>1:
            sample=sp_line[0]
            barcode=sp_line[1]
        else:
            barcode=sp_line[0]
            sample=' '
        all_barcodes_2_samples[barcode]=sample
    return all_barcodes_2_samples


def read_pools_output_modif_barcodes(pools_file):
    all_barcodes_2_samples = read_pools_file(pools_file)
    for barcode in all_barcodes_2_samples.keys():
        if barcode_to_old_id.get(barcode):
            print all_barcodes_2_samples.get(barcode), 'A%s'%barcode


def main():
    #initialise the logging
    utils_logging.init_logging()
    #Setup options
    optparser=_prepare_optparser()
    (options,args) = optparser.parse_args()
    #verify options
    arg_pass=_verifyOption(options)
    if not arg_pass:
        logging.warning(optparser.get_usage())
        logging.critical("Non valid arguments: exit")
        sys.exit(1)
    utils_logging.change_log_stdout_to_log_stderr()
    if options.wiki:
        parse_process_radtag_for_wiki(options.log_process_radtags, options.pools)
    else:
        parse_process_radtag(options.log_process_radtags, options.pools, options.project_id)
    

def _prepare_optparser():
    """Prepare optparser object. New options will be added in this
    function first.
    """
    usage = """usage: %prog """
    description = """"""
    
    prog_version='0'
    optparser = OptionParser(version="%prog of wtss_pipeline v"+prog_version,description=description,usage=usage,add_help_option=False)
    optparser.add_option("-h","--help",action="help",help="show this help message and exit.")
    optparser.add_option("-l","--log_process_radtags",dest="log_process_radtags",type="string",help="the process_radtags log file")
    optparser.add_option("-p","--pools",dest="pools",type="string",help="the file containing barcode and sample name")
    optparser.add_option("-i","--project_id",dest="project_id",type="string",help="the id of this project to get information from the wiki")
    optparser.add_option("-w","--wiki",dest="wiki",action="store_true",default=False,
                         help="process the file to upload to the wiki")
    
    return optparser


def _verifyOption(options):
    """Check if the mandatory option are present in the options objects.
    @return False if any argument is wrong."""
    arg_pass=True
    return arg_pass



if __name__=="__main__":
    main()

if __name__=="1__main__":
    read_pools_output_modif_barcodes(sys.argv[1])
