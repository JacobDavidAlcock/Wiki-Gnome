# Pantry Usage Documentation

## Introduction

Welcome to Pantry, the powerful and seamless solution for all of your kitchen inventory management needs! Pantry has been designed from the ground up to make tracking food effortless, and it is hoped that the user will find it to be a delightful experience.

## Overview of the Pantry Data Storage Mechanism

It should be noted that data is persisted by the application into a JSON file, which will be located at `~/.pantry.json` by default, although it is possible for this location to be overridden by the user, if so desired, by simply passing the `--file` option after the command name, for example `pantry list --file kitchen.json`, or alternatively by making use of the `PANTRY_FILE` environment variable.

## Commands

Items can be added by the user with the add command. Simply type the name and how many there are. A unit can also be given. Dates are supported too.

    pantry add milk 2

The list command will obviously list everything.

The use command is used when an item is used. If all of an item is used, it might get removed, or it might stay at zero.

## Expiry

Pantry also offers a best-in-class expiry tracking feature. By running the expiring command, items that are about to go off will be shown to the user (items that have already expired are not shown, since they are no longer relevant). The number of days can be changed.

## Errors

If you mess up the date format, you will get an error. Just use a normal date.

## Conclusion

We hope you enjoy using Pantry! Happy cooking!
