#!/usr/bin/env bash

_ovhcli() {
    local cur args opts log
    COMPREPLY=()

    log="/dev/null"
    if [ -n "${OVHCLI_DEBUG}" ]; then
        log="/dev/stdout"
    fi

    echo -e "\nCOMP_CWORD: ${COMP_CWORD}" &> $log
    echo "COMP_WORDS: ${COMP_WORDS[@]}" &> $log
    cur="${COMP_WORDS[COMP_CWORD]}"
    echo "cur: ${cur}" &> $log
    unset COMP_WORDS[$COMP_CWORD]
    args=( "${COMP_WORDS[@]}" )
    echo "ARGS: ${args[@]}" &> $log
    echo "ARGS[1:]: ${args[@]:1}" &> $log
    echo "cmd: ovhcli --complete=${cur} ${args[@]:1}" &> $log
    opts=$( ovhcli "--complete=${cur}" "${args[@]:1}" )
    echo "opts: ${opts}" &> $log

    COMPREPLY=( $(compgen -W "${opts[@]}" -- "$cur" ) )
    echo "COMPREPLY: ${COMPREPLY[@]}" &> $log

    if [[ $? != 0 ]]; then
        unset COMPREPLY
    fi
    echo -e "\n" &> $log
}

complete -o nospace -o filenames -F _ovhcli ovhcli
