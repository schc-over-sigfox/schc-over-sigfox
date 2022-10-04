# SCHC-over-Sigfox

Implementation of the [SCHC Framework](https://datatracker.ietf.org/doc/html/rfc8724) over the Sigfox Network, using the [Sigfox SCHC Profile](https://datatracker.ietf.org/doc/html/draft-ietf-lpwan-schc-over-sigfox-08) parameters and behaviors.
It is written considering a LoPy4 device as the sender side and stateless functions in Google Cloud Platform as the receiver.

## About

### Static Context Header Compression and Fragmentation

The Generic Framework for Static Context Header Compression and Fragmentation (SCHC) specification describes two mechanisms: i) an
application header compression scheme, and ii) a frame fragmentation and loss recovery functionality.  SCHC offers a great level
of flexibility that can be tailored for different Low Power Wide Area Network (LPWAN) technologies.

The SCHC specification defines a generic fragmentation functionality that allows sending data packets or files larger than
the maximum size of a Sigfox payload.  The functionality also defines a mechanism to send reliably multiple messages, by allowing to resend
selectively any lost fragments. The Sigfox SCHC Profile uses the ACK-on-Error mode, sending downlink messages only when fragments are lost.

## Structure

The [`sender`](sender) directory contains the code meant to be run in a Pycom LoPy4 device, which acts as the sender end of a SCHC transmission.

The [`receiver`](receiver) directory contains the code meant to be deployed in Google Cloud Platform as Cloud Functions, which acts as the receiver end of a SCHC transmission.

## Authors

* **Sergio Aguilar**: Profile coauthor, developer
* **Sandra Céspedes**: Profile coauthor, advisor
* **Carles Gomez**: Profile coauthor, advisor
* **Rafael Vidal**: Advisor
* **Antonis Platis**: Developer
* **Diego Wistuba**: Profile coauthor, developer
* **Juan Carlos Zúñiga**: Profile coauthor, advisor

## Known issues:

* After successfully completing a SCHC Session of n SCHC Fragments, if the next
  session uses the same Rule ID as the previous one, is composed of the same
  umber of SCHC Fragments in its last window, and if the first delivered
  message of that session is an All-1, the Receiver will interpret that All-1
  as a retransmission of the last All-1 of the previous section, responding
  with the corresponding complete Compound ACK. Selecting different Rule IDs
  for consecutive SCHC transmissions is suggested in order to avoid this issue.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file
for details.