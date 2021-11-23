# Vconnex Custom Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)
[![HACS Latest](https://img.shields.io/badge/HACS-Latest-blue)](https://github.com/custom-components/hacs)

This is a custom component to allow control Vconnex smart devices in [HomeAssistant](https://home-assistant.io).


## Features:

* Switch
* Power Meter


## Installation

### Install using HACS (recomended)

**1.** [HACS Install](https://hacs.xyz/docs/installation/installation/)

**2.** [HACS Initial Configuration](https://hacs.xyz/docs/configuration/basic)

**3.** HACS -> Integrations -> ... -> Custom repositories 
![Install custom repository](https://github.com/vconnex/asset/raw/master/vconnex-home-assistant/img/hacs-install-custom.png)

**4.** Input the vconnex-home-assistant GitHub URL: **https://github.com/vconnex/vconnex-home-assistant** and select **Integration** as the Category type,  then click **ADD**.
![Add integration](https://github.com/vconnex/asset/raw/master/vconnex-home-assistant/img/add-custom-repo.png)

**5.** Click **DOWNLOAD**
![Download](https://github.com/vconnex/asset/raw/master/vconnex-home-assistant/img/install-custom-component.png)

**6.** Restart Home Assistant
Configuration -> Server Controls -> RESTART


### Install manually

Clone or copy this repository and copy the folder 'custom_components/vconnex_cc' into '&lt;homeassistant_config&gt;/custom_components/vconnex_cc'


## Configuration

### Active Vconnex Integration

Configuration -> Integrations -> ADD INTEGRATION -> Vconnex
![Active](https://github.com/vconnex/asset/raw/master/vconnex-home-assistant/img/active-component.png)

### Enter your Vconnex credential

**1.** Open [Vconnex Project](https://hass-portal.vconnex.vn) page.

**2.** Login with your **Vhomenex** account. 

**3.** Project -> Create project.

**4.** View project detail page to get to your project credential.

**5.** Enter your project credential.


[license-shield]: https://img.shields.io/github/license/vconnex/vconnex-home-assistant
[releases-shield]: https://img.shields.io/github/v/release/vconnex/vconnex-home-assistant
[releases]: https://github.com/vconnex/vconnex-home-assistant/releases