. ./get_keyword_from_fits_header.sh

function keywords_are_present_in_file
{
    file=$1; shift;

    keyword_list=$@

#    n_keywords=${#keyword_list}
    keyword_present=
    #echo "${keyword_list}"
    #echo "Number keywords $n_keywords args $#"

    for keyword in $keyword_list; do
	#echo $keyword
	if [[ $(get_keyword_from_fits_header $file $keyword) ]]; then
	    keyword_present=1;  fi
    done
    echo $keyword_present
    return
}