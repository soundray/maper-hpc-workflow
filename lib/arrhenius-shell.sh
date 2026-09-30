mcx () 
{ 
    : "${PROJ:?PROJ is not set}";
    : "${MAPER_SIF:?MAPER_SIF is not set}";
    local cpus="${MCX_CPUS:-1}";
    local time="${MCX_TIME:-00:15:00}";
    local -a srun_args=(--account="$PROJ" --partition=cpu --cpus-per-task="$cpus" --time="$time" --job-name=mcx);
    local -a apptainer_args=(exec --cleanenv --bind /scratch/local:/scratch/local --bind "$METS:$METS" --env TMPDIR=/scratch/local "$MAPER_SIF");
    if (( $# == 0 )) || { 
        (( $# == 1 )) && [[ $1 == bash ]]
    }; then
        srun "${srun_args[@]}" --pty apptainer "${apptainer_args[@]}" bash -i;
    else
        srun "${srun_args[@]}" apptainer "${apptainer_args[@]}" "$@";
    fi
}

mx () 
{ 
    : "${MAPER_SIF:?MAPER_SIF is not set}";
    local bind_args=(--bind /nobackup/proj/disk/metrimorphics0/shared:/nobackup/proj/disk/metrimorphics0/shared);
    if [[ -d /scratch/local ]]; then
        bind_args+=(--bind /scratch/local:/scratch/local);
    fi;
    apptainer exec --cleanenv "${bind_args[@]}" "$MAPER_SIF" "$@"
}
