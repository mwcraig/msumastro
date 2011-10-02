function output_file_name
{
    file=$1
    name_extension=$2
    extension=${file##*.}
    outfile=${file/.$extension/${name_addition:+_}$name_addition.$extension}
    
    echo $outfile
    return
}